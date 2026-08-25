/*
 * Copyright (c) 2013, django CMS Association
 * Licensed under BSD
 * https://github.com/django-cms/django-cms
 *
 * The bundled jQuery 1.11.3 is a UMD script, not an ES module. Loading it for
 * its side effect installs window.jQuery, which this module re-exports so that
 * `import $ from 'jquery'` keeps working under vite.
 */

import '../../../../static/cms/js/libs/jquery.min.js';

const jQuery = window.jQuery;

export default jQuery;
export { jQuery };
