from django.conf import settings

WYM_TOOLS = "" + \
    "{'name': 'Bold', 'title': 'Strong', 'css': 'wym_tools_strong'},\n" +\
    "{'name': 'Italic', 'title': 'Emphasis', 'css': 'wym_tools_emphasis'},\n" +\
    "{'name': 'Superscript', 'title': 'Superscript', 'css': 'wym_tools_superscript'},\n" +\
    "{'name': 'Subscript', 'title': 'Subscript', 'css': 'wym_tools_subscript'},\n" +\
    "{'name': 'InsertOrderedList', 'title': 'Ordered_List', 'css': 'wym_tools_ordered_list'},\n" +\
    "{'name': 'InsertUnorderedList', 'title': 'Unordered_List', 'css': 'wym_tools_unordered_list'},\n" +\
    "{'name': 'Indent', 'title': 'Indent', 'css': 'wym_tools_indent'},\n" +\
    "{'name': 'Outdent', 'title': 'Outdent', 'css': 'wym_tools_outdent'},\n" +\
    "{'name': 'Undo', 'title': 'Undo', 'css': 'wym_tools_undo'},\n" +\
    "{'name': 'Redo', 'title': 'Redo', 'css': 'wym_tools_redo'},\n" +\
    "{'name': 'Paste', 'title': 'Paste_From_Word', 'css': 'wym_tools_paste'},\n" +\
    "{'name': 'ToggleHtml', 'title': 'HTML', 'css': 'wym_tools_html'},\n" 
    #"{'name': 'CreateLink', 'title': 'Link', 'css': 'wym_tools_link'},\n" +\
    #"{'name': 'Unlink', 'title': 'Unlink', 'css': 'wym_tools_unlink'},\n" +\
    #"{'name': 'InsertImage', 'title': 'Image', 'css': 'wym_tools_image'},\n" +\
    #"{'name': 'InsertTable', 'title': 'Table', 'css': 'wym_tools_table'},\n" +\
    #"{'name': 'Preview', 'title': 'Preview', 'css': 'wym_tools_preview'}"

WYM_TOOLS = getattr(settings, "WYM_TOOLS", WYM_TOOLS)

WYM_CONTAINERS = "" + \
    "{'name': 'P', 'title': 'Paragraph', 'css': 'wym_containers_p'}," +\
    "{'name': 'H1', 'title': 'Heading_1', 'css': 'wym_containers_h1'}," +\
    "{'name': 'H2', 'title': 'Heading_2', 'css': 'wym_containers_h2'}," +\
    "{'name': 'H3', 'title': 'Heading_3', 'css': 'wym_containers_h3'}," +\
    "{'name': 'H4', 'title': 'Heading_4', 'css': 'wym_containers_h4'}," +\
    "{'name': 'H5', 'title': 'Heading_5', 'css': 'wym_containers_h5'}," +\
    "{'name': 'H6', 'title': 'Heading_6', 'css': 'wym_containers_h6'}," +\
    "{'name': 'PRE', 'title': 'Preformatted', 'css': 'wym_containers_pre'}," +\
    "{'name': 'BLOCKQUOTE', 'title': 'Blockquote', 'css': 'wym_containers_blockquote'}," +\
    "{'name': 'TH', 'title': 'Table_Header', 'css': 'wym_containers_th'}"
    
WYM_CONTAINERS = getattr(settings, "WYM_CONTAINERS", WYM_CONTAINERS)

WYM_CLASSES = "" + \
    "{'name': 'date', 'title': 'PARA: Date', 'expr': 'p'}," +\
    "{'name': 'hidden-note', 'title': 'PARA: Hidden note', 'expr': 'p[@class!=\"important\"]'}"
    
WYM_STYLES = """
    {'name': '.hidden-note', 'css': 'color: #999; border: 2px solid #ccc;'},
    {'name': '.date', 'css': 'background-color: #ff9; border: 2px solid #ee9;'},
"""

WYM_CLASSES = getattr(settings, "WYM_CLASSES", WYM_CLASSES)
