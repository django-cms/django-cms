<?php

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
