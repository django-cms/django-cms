function append_h2_element_from_src (id) {
    var h2_elem = document.createElement('h2');

    h2_elem.id = id;
    h2_elem.textContent = 'id=' + id;
    document.body.appendChild(h2_elem);
}

append_h2_element_from_src('from_src_no_trigger');

document.addEventListener('DOMContentLoaded', function() {
    append_h2_element_from_src('from_src_needs_trigger_document_DOMContentLoaded');
});

window.addEventListener('DOMContentLoaded', function() {
    append_h2_element_from_src('from_src_needs_trigger_window_DOMContentLoaded');
});

window.addEventListener('load', function() {
    append_h2_element_from_src('from_src_needs_trigger_window_load');
});
console.log("SCRIPT LOADED")
