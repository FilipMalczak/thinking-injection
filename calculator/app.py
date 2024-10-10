from thinking_runtime.bootstrap import bootstrap

bootstrap()

if __name__=="__main__":
    import sys

    from thinking_injection.context.simple import SimpleContext
    from thinking_injection.typeset import from_package

    from calc.model.parser import RPNParser

    ctx = SimpleContext(from_package("calc"))
    with ctx.lifecycle() as index:
        parser = index.instance(RPNParser)
        expr = parser.parse(sys.argv[1:] or "1 2 + 4 * 5 -".split())
        print(expr, "=", expr.evaluate())
