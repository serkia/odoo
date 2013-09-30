# -*- coding: utf-8 -*-

from . import test_related
from . import test_new_fields
from . import test_onchange
from . import test_field_conversions
from . import test_model_scope  

fast_suite = [
]

checks = [
    test_related,
    test_model_scope,
    test_new_fields,
    test_onchange,
    test_field_conversions,
]
