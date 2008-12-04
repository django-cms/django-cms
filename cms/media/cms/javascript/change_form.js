$(document).ready(function() {
    $('#id_template').change(function() {
        var index = this.selectedIndex;
        var array = window.location.href.split('?');
        var query = $.query.set('template', this.options[index].value).toString();
        window.location.href=array[0]+query;
    });
    $('#id_language').change(function() {
        var index = this.selectedIndex;
        var array = window.location.href.split('?');
        var query = $.query.set('language', this.options[index].value).toString();
        window.location.href=array[0]+query;
    });
    document.getElementById("id_title").focus();
    var template = $.query.get('template');
    if(template) {
        $('#id_template').find("option").each(function() {
            this.selected = false;
            if (template==this.value)
                this.selected = true;
        })
    }
    $("#id_slug").change(function() { this._changed = true; });
    $("#id_title").keyup(function() {
        var e = $("#id_slug")[0];
        if (!e._changed) {
            e.value = URLify(this.value, 64);
        }
    });
    $('#traduction-helper-select').change(function() {
        var index = this.selectedIndex;
        if(index == 0) {
            $('#traduction-helper-content').hide(); return;
        }
        var array = window.location.href.split('?');
        $.get(array[0]+'traduction/'+this.options[index].value+'/', function(html) {
            $('#traduction-helper-content').html(html);
            $('#traduction-helper-content').show();
        });
    });
    $('.revisions-list a').click( function() {
        var link = this;
        $.get(this.href, function(html) {
            $('a', $(link).parent().parent()).removeClass('selected');
            $(link).addClass('selected');
            var form_row = $(link).parents('.form-row')[0];
            if($('a.disable', form_row).length) {
                $('iframe', form_row)[0].contentWindow.document.getElementsByTagName("body")[0].innerHTML = html;
            } else {
                var formrow_textarea = $('textarea', form_row);
                formrow_textarea.attr('value', html);
                // support for WYMeditor
                if (WYMeditor) {
                    $(WYMeditor.INSTANCES).each(function(i, wym) {
                        if (formrow_textarea.attr('id') === wym._element.attr('id')) {
                            wym.html(html);
                        }
                    });
                }
            }
        });
        return false;
    });
});