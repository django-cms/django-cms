# -*- coding: utf-8 -*-
import itertools

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import DummyModel


@plugin_pool.register_plugin
class DynamicJsLoadingPlugin(CMSPluginBase):
    model = DummyModel
    name = "DynamicJsLoading"
    render_template = "dynamic_js_loading/dynamic_js_loading.html"

    def render(self, context, instance, placeholder):
        """
        This generates a list of all 16 class usage permutations.
        originaly from https://stackoverflow.com/a/54059999
        >>> import itertools
        >>> l=[False,True]
        >>> list(itertools.product(l,repeat=4))

        [(False, False, False, False),
        (False, False, False, True),
        (False, False, True, False),
        (False, False, True, True),
        (False, True, False, False),
        (False, True, False, True),
        (False, True, True, False),
        (False, True, True, True),
        (True, False, False, False),
        (True, False, False, True),
        (True, False, True, False),
        (True, False, True, True),
        (True, True, False, False),
        (True, True, False, True),
        (True, True, True, False),
        (True, True, True, True)]

        """
        binary_list = [False, True]
        case_list = list(itertools.product(binary_list, repeat=4))
        context["js_test_classes"] = self.generate_class_string(
            *case_list[instance.testcase - 1]
        )

        return super(DynamicJsLoadingPlugin, self).render(
            context, instance, placeholder
        )

    def generate_class_string(
        self, execute_js, document_content, window_content, window_load
    ):
        """
        Generates the class string for the different test cases based on the truth values of the parameters

        Parameters
        ----------
        execute_js : bool
            Whether or not to use the class "cms-execute-js-to-render"

        document_content: bool
            Whether or not to use the class "cms-trigger-event-document-DOMContentLoaded"

        window_content: bool
            Whether or not to use the class "cms-trigger-event-window-DOMContentLoaded"

        window_load: bool
            Whether or not to use the class "cms-trigger-event-window-DOMContentLoaded"
        """
        full_class_list = [
            "cms-execute-js-to-render",
            "cms-trigger-event-document-DOMContentLoaded",
            "cms-trigger-event-window-DOMContentLoaded",
            "cms-trigger-event-window-load",
        ]
        include_list = [execute_js, document_content, window_content, window_load]
        class_list = []
        for include_bool, class_string in zip(include_list, full_class_list):
            if include_bool:
                class_list.append(class_string)
        return " ".join(class_list)
