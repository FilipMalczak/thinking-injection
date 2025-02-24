from thinking_runtime.defaults.recognise_runtime import register_facet, facet, envvar

register_facet(facet("DOCKER_DISABLED", envvar("DOCKER_DISABLED").is_present, envvar("DOCKER").equals("0")))