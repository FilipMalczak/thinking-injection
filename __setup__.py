from thinking_runtime.defaults.recognise_runtime import register_facet, facet, envvar

#todo add register_facet(<args as for facet>) overload
register_facet(facet("DOCKER_DISABLED", envvar("DOCKER_DISABLED").is_present, envvar("DOCKER").equals("0")))
register_facet(facet("CI", envvar("CI").is_present))