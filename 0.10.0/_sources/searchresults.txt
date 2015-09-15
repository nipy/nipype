.. This displays the search results from the Google Custom Search engine.
   Don't link to it directly.

Search results
==============

.. raw:: html

   <div id="cse" style="width: 100%;">Loading</div>
    <script src="http://www.google.com/jsapi" type="text/javascript"></script>
    <script type="text/javascript">
      function parseQueryFromUrl () {
        var queryParamName = "q";
        var search = window.location.search.substr(1);
        var parts = search.split('&');
        for (var i = 0; i < parts.length; i++) {
          var keyvaluepair = parts[i].split('=');
          if (decodeURIComponent(keyvaluepair[0]) == queryParamName) {
            return decodeURIComponent(keyvaluepair[1].replace(/\+/g, ' '));
          }
        }
        return '';
      }
      google.load('search', '1', {language : 'en', style : google.loader.themes.MINIMALIST});
      google.setOnLoadCallback(function() {
        var customSearchControl = new google.search.CustomSearchControl(
                '010960497803984932957:u8pmqf7fdoq');

        customSearchControl.setResultSetSize(google.search.Search.FILTERED_CSE_RESULTSET);
        customSearchControl.draw('cse');
        var queryFromUrl = parseQueryFromUrl();
        if (queryFromUrl) {
          customSearchControl.execute(queryFromUrl);
        }
      }, true);
    </script>
    <link rel="stylesheet" href="http://www.google.com/cse/style/look/default.css" type="text/css" /> <style type="text/css">
      .gsc-control-cse {
        font-family: Arial, sans-serif;
        border-color: #FFFFFF;
        background-color: #FFFFFF;
      }
      input.gsc-input {
        border-color: #BCCDF0;
      }
      input.gsc-search-button {
        border-color: #666666;
        background-color: #CECECE;
      }
      .gsc-tabHeader.gsc-tabhInactive {
        border-color: #E9E9E9;
        background-color: #E9E9E9;
      }
      .gsc-tabHeader.gsc-tabhActive {
        border-top-color: #FF9900;
        border-left-color: #E9E9E9;
        border-right-color: #E9E9E9;
        background-color: #FFFFFF;
      }
      .gsc-tabsArea {
        border-color: #E9E9E9;
      }
      .gsc-webResult.gsc-result,
      .gsc-results .gsc-imageResult {
        border-color: #FFFFFF;
        background-color: #FFFFFF;
      }
      .gsc-webResult.gsc-result:hover,
      .gsc-imageResult:hover {
        border-color: #FFFFFF;
        background-color: #FFFFFF;
      }
      .gs-webResult.gs-result a.gs-title:link,
      .gs-webResult.gs-result a.gs-title:link b,
      .gs-imageResult a.gs-title:link,
      .gs-imageResult a.gs-title:link b {
        color: #0000CC;
      }
      .gs-webResult.gs-result a.gs-title:visited,
      .gs-webResult.gs-result a.gs-title:visited b,
      .gs-imageResult a.gs-title:visited,
      .gs-imageResult a.gs-title:visited b {
        color: #0000CC;
      }
      .gs-webResult.gs-result a.gs-title:hover,
      .gs-webResult.gs-result a.gs-title:hover b,
      .gs-imageResult a.gs-title:hover,
      .gs-imageResult a.gs-title:hover b {
        color: #0000CC;
      }
      .gs-webResult.gs-result a.gs-title:active,
      .gs-webResult.gs-result a.gs-title:active b,
      .gs-imageResult a.gs-title:active,
      .gs-imageResult a.gs-title:active b {
        color: #0000CC;
      }
      .gsc-cursor-page {
        color: #0000CC;
      }
      a.gsc-trailing-more-results:link {
        color: #0000CC;
      }
      .gs-webResult .gs-snippet,
      .gs-imageResult .gs-snippet,
      .gs-fileFormatType {
        color: #000000;
      }
      .gs-webResult div.gs-visibleUrl,
      .gs-imageResult div.gs-visibleUrl {
        color: #008000;
      }
      .gs-webResult div.gs-visibleUrl-short {
        color: #008000;
      }
      .gs-webResult div.gs-visibleUrl-short {
        display: none;
      }
      .gs-webResult div.gs-visibleUrl-long {
        display: block;
      }
      .gsc-cursor-box {
        border-color: #FFFFFF;
      }
      .gsc-results .gsc-cursor-box .gsc-cursor-page {
        border-color: #E9E9E9;
        background-color: #FFFFFF;
        color: #0000CC;
      }
      .gsc-results .gsc-cursor-box .gsc-cursor-current-page {
        border-color: #FF9900;
        background-color: #FFFFFF;
        color: #0000CC;
      }
      .gs-promotion {
        border-color: #336699;
        background-color: #FFFFFF;
      }
      .gs-promotion a.gs-title:link,
      .gs-promotion a.gs-title:link *,
      .gs-promotion .gs-snippet a:link {
        color: #0000CC;
      }
      .gs-promotion a.gs-title:visited,
      .gs-promotion a.gs-title:visited *,
      .gs-promotion .gs-snippet a:visited {
        color: #0000CC;
      }
      .gs-promotion a.gs-title:hover,
      .gs-promotion a.gs-title:hover *,
      .gs-promotion .gs-snippet a:hover {
        color: #0000CC;
      }
      .gs-promotion a.gs-title:active,
      .gs-promotion a.gs-title:active *,
      .gs-promotion .gs-snippet a:active {
        color: #0000CC;
      }
      .gs-promotion .gs-snippet,
      .gs-promotion .gs-title .gs-promotion-title-right,
      .gs-promotion .gs-title .gs-promotion-title-right *  {
        color: #000000;
      }
      .gs-promotion .gs-visibleUrl,
      .gs-promotion .gs-visibleUrl-short {
        color: #008000;
      }
      /* Manually added - the layout goes wrong without this */
      .gsc-tabsArea,
      .gsc-webResult:after,
      .gsc-resultsHeader {
         clear: none;
      }
    </style>