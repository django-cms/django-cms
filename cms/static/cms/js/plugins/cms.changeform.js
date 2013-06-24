/*##################################################|*/
/* #CMS# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {

	// hide rows when hidden input fields are added
	$('input[type="hidden"]').each(function () {
		$(this).parent('.form-row').hide()
	});

	// set slugify for titles
	var title= $('#id_title');
	var slug = $('#id_slug');
	if (title.length > 0 && slug.length > 0) {
		var update = function(){
			var value = title.val();
			if (window.UNIHANDECODER){
				value = UNIHANDECODER.decode(value);
			}
			slug.val(URLify(value, 64));
		};
		title.keyup(update);
		update();
	}

});
})(CMS.$);




(function ($) {
    $(document).ready(function () {




        var new_slug = true;
        var slug = $('#id_slug')
        if (slug.length && slug[0].value) {
            new_slug = false;
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
})(django.jQuery);
