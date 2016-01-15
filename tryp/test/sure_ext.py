from pathlib import Path

import sure

from tryp import Maybe, Empty, Just


class AssBuilder(sure.AssertionBuilder):

    @sure.assertionmethod
    def contain(self, what):
        if isinstance(self.obj, Maybe):
            return self.just_contain(what)
        else:
            return super().contain(what)

    @sure.assertionmethod
    def just_contain(self, what):
        self.obj.should.be.a(Maybe)
        if self.negative:
            msg = "{} contains {}, expected {}"
            assert self.obj.is_empty or self.obj._get != what,\
                msg.format(self.obj, self.obj._get, what)
        else:
            self.be.just
            self.obj._get.should.equal(what)
        return True

    def _bool(self, pred, agent, action):
        no = ('not ' if self.negative else '') + 'to '
        assert pred(self.obj) ^ self.negative,\
            'expected {} \'{}\' {} {}'.format(agent, self.obj, no, action)
        return True

    def just(self):
        return self.be.a(Just)

    def empty(self):
        if isinstance(self.obj, Maybe):
            return self.be.a(Empty)
        else:
            return super().empty()

    @sure.assertionproperty
    def exist(self):
        err = "can only check existence of Path, not {}"
        assert isinstance(self.obj, Path), err.format(self.obj)
        return self._bool(lambda a: a.exists(), "path", "exist")

    @sure.assertionmethod
    def start_with(self, prefix):
        return self.match('^{}'.format(prefix))


def install_assertion_builder(builder):
    sure.AssertionBuilder = builder

__all__ = ('install_assertion_builder', 'AssBuilder')
