Imprortant!
------------
Spell Checker “WSC” dialog plugin for CKEditor 4 **approached its end-of-life (EOL) on December 31, 2021**. Find out more in our [blog post](https://webspellchecker.com/blog/2020/12/02/end-of-life-for-spell-checker-dialog-plugin-for-ckeditor-4/) about its termination schedule.

The effect of termination: the spell checking doesn't work, there is an incessant loading spinner on the dialog. Check [here](https://github.com/WebSpellChecker/ckeditor-plugin-wsc/issues/67) how to remove the plugin.


WebSpellChecker Dialog plugin for CKEditor 4
===============================

WebSpellChecker Dialog (WSC Dialog) provides distraction-free proofreading, checking the whole text’s spelling and grammar on-click in a separate pop-up window.

![WSC Dialog Plugin for CKEditor 4 View](https://webspellchecker.com/app/images/wsc_dialog_plugin_for_ckeditor4.png)

This plugin brings the multi-language WSC Dialog functionality into CKEditor 4. It is integrated by default starting with [Standard Package of CKEditor 4](https://ckeditor.com/ckeditor-4/download/). You can find it on the CKEditor 4 toolbar panel under the ABC button (Check Spelling).

If your version of CKEditor doesn’t have WSC Dialog built-in, you can easily add it by following the steps outlined in the Get Started section.

The default version of WSC Dialog plugin for CKEditor 4 is using the free services of WebSpellChecker. It is provided with a banner ad and has some [limitations](https://docs.webspellchecker.net/display/WebSpellCheckerCloud/Free+and+Paid+WebSpellChecker+Cloud+Services+Comparison+for+CKEditor).

To lift the limitations and get rid of the banner, [obtain a license](https://webspellchecker.com/wsc-dialog-ckeditor4/#pricing). Depending on your needs, you can choose a Cloud-based or Server (self-hosted) solution.

Demo
------------
WSC Dialog plugin for CKEditor 4: https://webspellchecker.com/wsc-dialog-ckeditor4/

Supported languages
------------

The WSC Dialog plugin for CKEditor as a part of the free services supports the next languages for check spelling: American English, British English, Canadian English, Canadian French, Danish, Dutch, Finnish, French, German, Greek, Italian, Norwegian Bokmal, Spanish, Swedish.

There are also additional languages and specialized dictionaries available for a commercial license, you can check the full list [here](https://webspellchecker.com/additional-dictionaries/).

Get started
------------

1. Clone/copy this repository contents in a new "plugins/wsc" folder in your CKEditor installation.
2. Enable the "wsc" plugin in the CKEditor configuration file (config.js):

        config.extraPlugins = 'wsc';

That's all. WSC Dialog will appear on the editor toolbar under the ABC button and will be ready to use.

Supported browsers
-------

This is the list of officially supported browsers for the WSC Dialog plugin for CKEditor 4. WSC Dialog may also work in other browsers and environments but we unable to check all of them and guarantee proper work.

* Chrome (the latest)
* Firefox (the latest)
* Safari (the latest)
* MS Edge (the latest)
* Internet Explorer 8.0 (limited support)
* Internet Explorer 9.0+ (close to full support)

Note: All browsers are to be supported for web pages that work in Standards Mode.

Resources
-------

* Demo: https://webspellchecker.com/wsc-dialog-ckeditor4/
* Documentation: https://docs.webspellchecker.net/
* YouTube video: https://youtu.be/bkVPZ-5T22Q
* Term of Service: https://webspellchecker.com/terms-of-service/

Technical support or questions
-------

In cooperation with the CKEditor team, during the past 10 years we have simplified the installation and built the extensive amount of documentation devoted to WSC Dialog plugin for CKEditor 4 and less.

If you are experiencing any difficulties with the setup of the plugin, please check the links provided in the Resources section.

Holders of an active subscription to the services or a commercial license have access to professional technical assistance directly from the WebSpellChecker team. [Contact us here](https://webspellchecker.com/contact-us/)!

Reporting issues
-------

Please use the [WSC Dialog plugin for CKEditor 4 GitHub issue page](https://github.com/WebSpellChecker/ckeditor-plugin-wsc/issues) to report bugs and feature requests. We will do our best to reply at our earliest convenience.

License
-------

This plugin is licensed under the terms of any of the following licenses at your choice: [GPL](http://www.gnu.org/licenses/gpl.html), [LGPL](http://www.gnu.org/licenses/lgpl.html) and [MPL](http://www.mozilla.org/MPL/MPL-1.1.html).

See LICENSE.md for more information.

Developed by [WebSpellChecker](https://webspellchecker.com/) in cooperation with CKSource.
