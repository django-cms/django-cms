<?php

// SECURITY WARNING: read the comment below before removing this line!
die ('This functionality is disabled by default. Please see plugins/tidy/tidy.php for additional information on how to setup Tidy.');

/*

 WARNING: ENABLING THIS FILE IS NOT SECURE!

 Generally speaking, it is a bad idea to have a script that outputs what you send it.
 It could easily be used to steal cookies from you, for instance if:
  www.badsite.com has a hidden IFRAME with SRC="/path/to/tidy.php?html="+escape("... some JavaScript that sends your cookies to badsite.org ...")

 You could filter out <script> tags, onclick, onblur, onload, onmouseover... attributes
 if you *really* need this functionality. Or, even better, you could allow only the tags and
 attributes that you explicitly allow (future versions of WYMeditor might provide this
 functionality by default - please contribute).

 Be warned that providing authentication is NOT enough to guard you agains the attack. When
 someone is authenticated in your page and visits www.badsite.com, the IFRAME has the proper
 authentication so nothing has changed.

*/

if (get_magic_quotes_gpc()) $html = stripslashes($_REQUEST['html']);
else $html = $_REQUEST['html'];

if(strlen($html) > 0) {

  // Specify configuration
  $config = array(
            'bare'                        => true,
            'clean'                       => true,
            'doctype'                     => 'strict',
            'drop-empty-paras'            => true,
            'drop-font-tags'              => true,
            'drop-proprietary-attributes' => true,
            'enclose-block-text'          => true,
            'indent'                      => false,
            'join-classes'                => true,
            'join-styles'                 => true,
            'logical-emphasis'            => true,
            'output-xhtml'                => true,
            'show-body-only'              => true,
            'wrap'                        => 0);

  // Tidy
  $tidy = new tidy;
  $tidy->parseString($html, $config, 'utf8');
  $tidy->cleanRepair();

  // Output
  echo $tidy;
} else {

echo ('0');
}
?>
