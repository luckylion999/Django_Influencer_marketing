/**
  This module contains functions available to the
  global scope.
**/

function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    var expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

var onDomIsRendered = function(domString) {
  return new Promise(function(resolve, reject) {
    function waitUntil() {
      setTimeout(function() {
        if ($(domString).length > 0) {
          resolve($(domString));
        } else {
          waitUntil();
        }
      }, 100);
    }

    waitUntil();
  });
};

/**
 * @brief Wait for something to be ready before triggering a timeout
 * @param {callback} isready Function which returns true when the thing we're waiting for has happened
 * @param {callback} success Function to call when the thing is ready
 * @param {callback} error Function to call if we time out before the event becomes ready
 * @param {int} count Number of times to retry the timeout (default 300 or 6s)
 * @param {int} interval Number of milliseconds to wait between attempts (default 20ms)
 */
function waitUntil(isready, success, error, count, interval) {
    if (count === undefined) {
        count = 300;
    }
    if (interval === undefined) {
        interval = 20;
    }
    if (isready()) {
        success();
        return;
    }
    // The call back isn't ready. We need to wait for it
    setTimeout(function() {
        if (!count) {
            // We have run out of retries
            if (error !== undefined) {
                error();
            }
        } else {
            // Try again
            waitUntil(isready, success, error, count - 1, interval);
        }
    }, interval);
}

$(window).scroll(function() {
  if ($(document).scrollTop() > 50) {
    $('.navbar').addClass('shrink');
  } else {
    $('.navbar').removeClass('shrink');
  }
});

/**

// Set trianglify background
(function() {

    if($('#searchPanel').length > 0) {
        onDomIsRendered("#homePanelTableDiv").then(function(element){

            var target = document.getElementById('trianglify-js');
            var pattern = Trianglify({
                width: window.innerWidth, 
                height: window.innerHeight,
                //x_colors: ['#e3f4fb', '#a9d4e7', '#f2e5f2', '#97BDD1', '#e5cce5', '#A7D1E8', '#B8E6FF'],
                x_colors: ['#48c9ef', '#c9f5fe', '#A7D1E8', '#B8E6FF'],
                y_colors: 'match_x',
            });
            target.style['background-image'] = 'url(' + pattern.png() + ')';

        });
    } else {

        onDomIsRendered("main").then(function(element){

            var target = document.getElementById('trianglify-js');
            var pattern = Trianglify({
                width: window.innerWidth, 
                height: window.innerHeight,
                x_colors: ['#e3f4fb', '#a9d4e7', '#f2e5f2', '#97BDD1', '#e5cce5', '#A7D1E8', '#B8E6FF'],
                y_colors: 'match_x',
            });
            target.style['background-image'] = 'url(' + pattern.png() + ')';

        });
    }

})();
*/