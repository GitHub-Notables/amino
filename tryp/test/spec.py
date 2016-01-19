import os

import tek  # type: ignore

import tryp
from tryp.logging import tryp_stdout_logging
from tryp.test.sure_ext import install_assertion_builder, AssBuilder


class Spec(tek.Spec):

    def setup(self, *a, **kw):
        tryp.development = True
        tryp_stdout_logging()
        install_assertion_builder(AssBuilder)
        super(Spec, self).setup(*a, **kw)


class IntegrationSpec(Spec):

    def setup(self, *a, **kw):
        os.environ['PROTEOME_INTEGRATION'] = '1'
        tryp.integration_test = True
        super().setup(*a, **kw)

__all__ = ('Spec', 'IntegrationSpec')
