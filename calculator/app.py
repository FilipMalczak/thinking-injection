from thinking_runtime.bootstrap import bootstrap

bootstrap()

if __name__=="__main__":
    import sys


    from thinking_injection.scope import ContextScope

    from thinking_injection.context import BasicContext
    from thinking_injection.typeset import from_package

    from calc.model.parser import RPNParser

    ctx = BasicContext(ContextScope.of(*from_package("calc")))
    with ctx.lifecycle():
        parser = ctx.instance(RPNParser)
        expr = parser.parse(sys.argv[1:] or "1 2 + 4 * 5 -".split())
        print(expr, "=", expr.evaluate())