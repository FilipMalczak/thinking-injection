from collections import defaultdict
from contextlib import contextmanager
from logging import getLogger
from typing import Optional

from thinking_modules.model import ModuleName

from thinking_injection.common.exceptions import UnknownTypesException
from thinking_injection.context.configurable.configurator import ContextConfigurator, ConfiguratorPhaseMismatchException
from thinking_injection.context.configurable.phase import ConfigurationPhase
from thinking_injection.context.protocol import ApplicationContext, InstanceIndex
from thinking_injection.context.simple import SimpleContext, _InstanceIndexLoopback
from thinking_injection.exceptions import InvalidInternalTypeException
from thinking_injection.ordering import TypeComparator
from thinking_injection.registry.delegating import TypeIndexUnion
from thinking_injection.registry.protocol import DiscoveredTypes, TypeIndex
from thinking_injection.typeset import ImmutableTypeSet, AnyTypeSet, from_package
from thinking_programming.collectable import Collectable, collect

log = getLogger(__name__)


CONFIGURATION_TYPES = frozenset({
    ConfigurationPhase,
    ContextConfigurator
})


def is_configuration_item[T: type](t: T) -> bool:
    return issubclass(t, tuple(CONFIGURATION_TYPES))


class ConfiguredIndex(InstanceIndex):
    def __init__(self, configurators_context: ApplicationContext, business_context: SimpleContext):
        self.configurators_context = configurators_context
        self.business_context = business_context
        self._raw_manager = self._both_contexts_lifecycle_manager()
        self.configurators_index: InstanceIndex = None
        self.business_index: InstanceIndex = None

    def instance[T](self, t: type[T]) -> Optional[T]:
        index = self.configurators_index if is_configuration_item(t) else self.business_index
        return index.instance(t)

    def instances[T](self, t: type[T]) -> frozenset[T]:
        index = self.configurators_index if is_configuration_item(t) else self.business_index
        return index.instances(t)

    @contextmanager
    def _both_contexts_lifecycle_manager(self):
        log.info("Entering context of config index")
        with self.configurators_context.lifecycle() as config_index:
            self.configurators_index = config_index
            ordered_phases: list[ConfigurationPhase] = []
            configurator_per_phase: dict[ConfigurationPhase, list[ContextConfigurator]] = defaultdict(list)
            for ct in self.configurators_context.type_index().order():
                instance = config_index.instance(ct)
                if isinstance(instance, ConfigurationPhase):
                    ordered_phases.append(instance)
                elif isinstance(instance, ContextConfigurator):
                    ConfiguratorPhaseMismatchException.guard(instance)
                    configurator_per_phase[instance.phase()].append(instance)
                else:
                    log.debug(f"Not a configuration phase, nor a configurator: {instance}")
            log.info(f"Ordered phases: {ordered_phases}")
            log.info("Customizers per phase:")
            for k, v in configurator_per_phase.items():
                log.info(f"{k}: {v}")
            customizer = self.business_context.registry.customizer()
            for phase in ordered_phases:
                for configurator in configurator_per_phase[phase]:
                    log.info(f"Running {configurator}")
                    configurator.configure_context(customizer)
            log.info("Entering context of business index")
            with self.business_context.lifecycle() as business_index:
                self.business_index = business_index
                yield

    def __enter__(self):
        self._raw_manager.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        result = self._raw_manager.__exit__(exc_type, exc_value, traceback)
        return result

    def type_index(self) -> TypeIndex:
        return TypeIndexUnion(
            [self.configurators_index.type_index(), self.business_index.type_index()],
            ["configuration", "business"]
        )


class ConfigurableContext(ApplicationContext[ConfiguredIndex]):
    def __init__(self, typeset: AnyTypeSet = None, cyclic_resolver: TypeComparator = None):
        default_configurators_typeset = from_package(ModuleName.of(__name__).parent)
        self.configurators_context = SimpleContext(default_configurators_typeset, cyclic_resolver=cyclic_resolver)
        self.business_context = SimpleContext(cyclic_resolver=cyclic_resolver)
        self.register(typeset)

    def register(self, *t: Collectable[type]) -> DiscoveredTypes:
        out = set()
        for x in collect(type, *t):
            ctx = self.configurators_context if is_configuration_item(x) else self.business_context
            result = ctx.register(x)
            out.update(result)
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

    def lifecycle(self) -> ConfiguredIndex:
        return ConfiguredIndex(self.configurators_context.clone(), self.business_context.clone())
