from collections import defaultdict
from contextlib import contextmanager
from typing import Optional

from thinking_injection.context.configurable.configurator import ContextConfigurator, declares_allowed_phase
from thinking_injection.registry.customizable.customizer import TypeRegistryCustomizer, ImplementationsCustomizer, \
    TypeImplementationsCustomizer
from thinking_injection.common.exceptions import UnknownTypesException, UnknownTypeException
from thinking_injection.context.configurable.phase import ConfigurationPhase
from thinking_injection.context.protocol import ApplicationContext, InstanceIndex
from thinking_injection.context.simple import SimpleContext
from thinking_injection.registry.delegating import TypeIndexUnion
from thinking_injection.registry.protocol import DiscoveredTypes, TypeIndex
from thinking_injection.typeset import ImmutableTypeSet

from thinking_programming.collectable import Collectable, collect

CONFIGURATION_TYPES = frozenset({
    ConfigurationPhase,
    ContextConfigurator
})

def is_configuration_item[T: type](t: T) -> bool:
    return issubclass(t, tuple(CONFIGURATION_TYPES))

class CustomizedIndex(InstanceIndex):
    def __init__(self, configurators_context: ApplicationContext, businesss_context: SimpleContext):
        self.configurators_context = configurators_context
        self.business_context = businesss_context
        self._raw_manager = self._both_contexts_lifecycle_manager()
        self.configurators_index: InstanceIndex = None
        self.business_index: InstanceIndex = None

    #TODO
    def instance[T](self, t: type[T]) -> Optional[T]:
        index = self.configurators_index if is_configuration_item(t) else self.business_index
        return index.instance(t)

    def instances[T](self, t: type[T]) -> frozenset[T]:
        index = self.configurators_index if is_configuration_item(t) else self.business_index
        return index.instances(t)

    @contextmanager
    def _both_contexts_lifecycle_manager(self):
        with self.configurators_context.lifecycle() as config_index:
            self.configurators_index = config_index
            ordered_phases: list[ConfigurationPhase] = []
            configurator_per_phase: dict[ConfigurationPhase, set[ContextConfigurator]] = defaultdict(set)
            for ct in self.configurators_context.type_index().order():
                instance = config_index.instance(ct)
                if isinstance(instance, ConfigurationPhase):
                    ordered_phases.append(instance)
                else:
                    assert isinstance(instance, ContextConfigurator)
                    assert declares_allowed_phase(instance)
                    configurator_per_phase[instance.phase()].add(instance)
            customizer = self.business_context.customizer()
            for phase in ordered_phases:
                for configurator in configurator_per_phase[phase]:
                    configurator.configure_context(customizer)
            with self.business_context.lifecycle() as business_index:
                self.business_index = business_index
                yield

    #//todo

    def __enter__(self):
        return self._raw_manager.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        result = self._raw_manager.__exit__(exc_type, exc_value, traceback)
        return result


class CustomizableContext(ApplicationContext[CustomizedIndex]):
    def __init__(self):
        self.configurators_context = SimpleContext()
        self.business_context = SimpleContext()

    def register(self, *t: Collectable[type]) -> DiscoveredTypes:
        out = set()
        for x in collect(type, *t):
            ctx = self.configurators_context if is_configuration_item(x) else self.business_context
            out.update(ctx.register(x))
        return frozenset(out)

    def remove(self, *t: Collectable[type]):
        configurators = []
        business = []
        for x in collect(type, *t):
            target = configurators if is_configuration_item(x) else business
            target.append(x)
        unknowns = []
        try:
            self.configurators_context.remove(*configurators)
        except UnknownTypesException as e:
            unknowns.extend(e.unknown_types)
        try:
            self.business_context.remove(*business)
        except UnknownTypesException as e:
            unknowns.extend(e.unknown_types)
        if unknowns:
            raise UnknownTypesException("Cannot remove types from customizable context", unknowns)

    def known_types(self) -> ImmutableTypeSet:
        return self.configurators_context.known_types().union(self.business_context.known_types())

    def type_index(self) -> TypeIndex:
        return TypeIndexUnion([self.configurators_context, self.business_context])

    def lifecycle(self) -> CustomizedIndex:
        return CustomizedIndex(self.configurators_context.clone(), self.business_context.clone())