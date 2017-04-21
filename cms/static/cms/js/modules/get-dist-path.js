var getDistPath = function (scriptFileName) {
    var fileNameReplaceRegExp = new RegExp(scriptFileName + '.*$', 'gi');

    if (document.currentScript) {
        return document.currentScript.src.replace(fileNameReplaceRegExp, '');
    }
    var scripts;
    var scriptUrl;
    var getSrc = function (listOfScripts, attr) {
        var fileName;
        var scriptPath;

        for (var i = 0; i < listOfScripts.length; i++) {
            scriptPath = null;
            if (listOfScripts[i].getAttribute.length !== undefined) {
                scriptPath = listOfScripts[i].getAttribute(attr, 2);
            }
            if (!scriptPath) {
                continue; // eslint-disable-line
            }
            fileName = scriptPath;
            fileName = fileName.split('?')[0].split('/').pop(); // get script filename
            if (fileName === scriptFileName) {
                return scriptPath;
            }
        }
    };

    scripts = document.getElementsByTagName('script');
    scriptUrl = getSrc(scripts, 'src');
    if (scriptUrl) {
        return scriptUrl.replace(fileNameReplaceRegExp, '');
    }
    return '';
};

module.exports = getDistPath;
