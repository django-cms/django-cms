(function ($) {
    $(document).ready(function () {
        var new_slug = true;
        var slug = $('#id_slug')
        if (slug.length && slug[0].value) {
            new_slug = false;
        }

        if (window.location.href.split("history").length == 1 && window.location.href.split("recover").length == 1) {
            $.each(["template"], function (i, label) {
                var select = $('select#id_' + label);
                select.change(function () {
                    var changed = $("#id_slug")[0]._changed;

                    if ($("#id_title")[0]._changed) {
                        changed = true;
                    }
                    var pub = $("#id_published");
                    if (pub.length) {
                        if (pub[0]._changed) {
                            changed = true;
                        }
                    }
                    if ($('iframe').length) {
                        changed = true;
                    }
                    var answer = '';
                    var array = window.location.href.split('?');
                    var query = $.query.set(label, this.options[this.selectedIndex].value).toString();
                    if (changed) {
                        var question = gettext("Are you sure you want to change the %(field_name)s without saving the page first?");
                        answer = confirm(interpolate(question, {
                            field_name: select.prev().text().slice(0, -1)
                        }, true));
                    } else {
                        answer = true;
                    }

                    if (answer) {
                        window.location.href = array[0] + query;
                    }

                });
            });
        }

        $("#id_title").focus();
        $("#id_slug").change(function () {
            this._changed = true;
        });
        $('#id_title').change(function () {
            this._changed = true;
        });
        $('#id_published').change(function () {
            this._changed = true;
        });
        $("#id_title").keyup(function () {
            var e = $("#id_slug")[0];
            if (!e._changed && new_slug) {
                var value = this.value;
                if (window.UNIHANDECODER) {
                    value = UNIHANDECODER.decode(value);
                }
                e.value = URLify(value, 64);
            }
        });

        // inline group loader
        $('div.loading').each(function () {
            var url = $(this).attr("rel")
            $(this).load(url);
        });

    });

    // global functions
    trigger_lang_button = function (e, url) {
        // also make sure that we will display the confirm dialog
        // in case users switch tabs while editing plugins
        var changed = false;
        var question = '';
        var answer = '';
        var slug = $("#id_slug")
        if (slug.length) {

            if (slug[0]._changed) {
                changed = true;
            }

            if ($("#id_title")[0]._changed) {
                changed = true;
            }

        }

        if (changed) {
            question = gettext("Are you sure you want to change tabs without saving the page first?");
            answer = confirm(question);
        } else {
            answer = true;
        }

        if (!answer) {
            return false;
        } else {
            window.location = url;
        }
    }
})
    (jQuery);
