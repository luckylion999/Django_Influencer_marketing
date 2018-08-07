(function() {

var htmlElem = $('html');

var age_group_data = [];
var gender_data = [];
var engagement_data = [];
var followers_data = [];
var engagement_average_data = [];
var engagement_percent;
var engagement_average;
var age_group_chart;
var gender_chart;
var engagement_chart;
var followers_chart;
var trends_cols = [];
var trends_x_axis = [];

google.charts.load('current', {
    'packages':['geochart'],
    'mapsApiKey': 'AIzaSyDCwyzwF0NsAh37hZ8meIFo0tKSQgRsEDw'
});
var country_data = [];

function round(value, decimals) {
  return Number(Math.round(value+'e'+decimals)+'e-'+decimals);
}

function loadNewData() {

    if(age_group_chart) {
        // load data with time offset
        age_group_chart.load({
            columns: age_group_data
        });
    }
    if(gender_chart) {
        gender_chart.load({
            columns: gender_data
        });
    }
    if(engagement_chart) {
        if(engagement_percent > 0) {
            engagement_data = [];
            engagement_data.push(['Engagement percent', engagement_percent]);
            engagement_chart.load({
                columns: [
                        ['percent', engagement_percent],
                        ['average', engagement_average]
                      ]
            });
        } else {
            // remove the engagement chart if engagement percent is <= 0
            $('#engagement_chart_col').css('display','none');
        }
    }

    if(followers_chart) {
        followers_chart.load({
            columns: followers_data
        });
    }

    PageElements.hideTopPanelLoader();
}

/**
    Make profile picture
*/
function getProfilePic() {

    PageElements.showMainLoader();
    $.get(profile_pic_url, function(data, status) {

        if(data.status == 200 && data.profile_pic_url) {
            $('.user_img').attr('src', data.profile_pic_url);
        } else {
            $('.user_img').attr('src', anon_profile_path);
            return null;
        }
    }).fail(function() {
        $('.user_img').attr('src', anon_profile_path);
    }).done(function() {
        PageElements.hideMainLoader();
        makeAgeGroupChart();
    });
}

function makeAgeGroupChart() {

    $.get(age_group_url, function(data, status) {
        if(data.is_auth_user == false) {
            PageElements.hideTopPanelLoader();
            $('#age_group_chart').html('<p>Please login to view full report.</p>');
        } else {

            if (data.status == 200) {
                if (!data.age_group_stats) {
                    makeEngagementChart();
                    return;
                }

                $('#age_group_chart').prev().html('<h4>Age groups</h4>');

                // make age group chart data
                for (var key in data.age_group_stats) {

                    if (data.age_group_stats.hasOwnProperty(key)) {
                        if (data.age_group_stats[key] !== 0) {
                            var tmp_col = [key];
                            tmp_col.push(data.age_group_stats[key]);
                            age_group_data.push(tmp_col);
                        }
                    }
                }
                age_group_data = age_group_data.sort();
                // make age group chart
                age_group_chart = c3.generate({
                    bindto: '#age_group_chart',
                    data: {
                        columns: [],
                        type: 'pie',
                        order: null,
                    },
                    size: {
                        height: 200
                    },
                });

            } else {
                PageElements.hideTopPanelLoader();
                $('#age_group_chart').html('<p>Data not yet available for this influencer.</p>');
            }
        }

        makeGenderChart();
    });
}

function makeGenderChart() {
    $.get(gender_url, function(data, status){
        if(data.is_auth_user == false) {
            PageElements.hideTopPanelLoader();
            $('#gender_chart').html('<p>Please login to view full report.</p>');
        } else {
            if (data.status == 200) {

                $('#gender_chart').prev().html('<h4>Gender distribution</h4>');

                // make gender chart data
                for (var key in data.gender_stats) {

                    if (data.gender_stats.hasOwnProperty(key)) {
                        var tmp_col;
                        if (key === 'M') {
                            tmp_col = ['Male'];
                        }
                        else {
                            tmp_col = ['Female'];
                        }

                        tmp_col.push(data.gender_stats[key]);
                        gender_data.push(tmp_col);
                    }
                }

                // make gender chart
                gender_chart = c3.generate({
                    bindto: '#gender_chart',
                    data: {
                        columns: [
                            ['Male', 0],
                            ['Female', 0],
                        ],
                        type: 'pie',
                        colors: {
                            'Male': '#597CE7',
                            'Female': '#8858E9'
                        }
                    },
                    size: {
                        height: 200
                    }
                });

            } else {
                PageElements.hideTopPanelLoader();
                $('#gender_chart').html('<p>Data not yet available for this influencer.</p>');
            }
        }

        makeEngagementChart();
    });
}

function makeEngagementChart() {
    $.get(engagement_url, function(data, status) {

        if(data.is_auth_user == false) {
            PageElements.hideTopPanelLoader();
            $('#engagement_chart').html('<p>Please login to view full report.</p>');
        } else {
            if(data.status == 200) {

                $('#engagement_chart').prev().html('<h4>Engagement Status</h4>');

                engagement_percent = Math.min(round(data.engagement_stats * 100, 2), 10);
                engagement_average = Math.min(round(data.average_engagement * 100, 2), 10);
                engagement_chart = c3.generate({
                    bindto: '#engagement_chart',
                    data: {
                        columns: [
                            ['percent', engagement_percent],
                            ['average', engagement_average]
                        ],
                        types: {
                            'percent': 'bar'
                        }
                    },
                    size: {
                        height: 200
                    },
                    bar: {
                        width: {
                            ratio: 0.3
                        }
                    },
                    axis: {
                        x: {
                            type: 'category',
                            tick: {
                                values: ['']
                            }
                        }
                    },
                    tooltip: {
                        format: {
                            title: function (d) { return ''}
                        }
                    }
                });
                // make age group chart data

            } else {
                PageElements.hideTopPanelLoader();
                $('#loader-background').css('display', 'none');
            }
        }


        makeFollowersTrendGraph();
    });
}

function makeFollowersTrendGraph() {

    $.get(followers_trend_url, function(data, status) {
        if(data.is_auth_user == false) {
            PageElements.hideTopPanelLoader();
            $('#followers_trend_chart').html('<p>Please login to view full report.</p>');
        } else {
            if (data.status == 200) {

                // parse data
                followers_data = [['followers',]];
                var x_axis = [];

                var tmp = data.followers_trend_stats;
                for (var i = 0; i < tmp.length; i++) {
                    x_axis.push(tmp[i][0]);
                    followers_data[0].push(tmp[i][1]);
                }

                $('#followers_trend_chart').prev().html('<h4>Followers</h4>');
                followers_chart = c3.generate({
                    bindto: '#followers_trend_chart',
                    data: {
                        columns: [],
                        type: 'bar'
                    },
                    bar: {
                        width: {
                            ratio: 0.5
                        }
                    },
                    size: {
                        height: 200
                    },
                    axis: {
                        x: {
                            type: 'category',
                            categories: x_axis,
                        }
                    },
                    legend: {
                        show: false
                    },
                    tooltip: {
                        format: {
                            value: function (value) {
                                return d3.format(",")(value);
                            }
                        }
                    },
                });
            }
        }

        PageElements.showTopPanel();
        loadNewData();

        // go to the next panel
        var firstGeoRun = 1;
        setInterval(function() {
        	if(firstGeoRun) {
        		firstGeoRun = 0;
        		google.charts.setOnLoadCallback(drawRegionsMap);
        	}
        }, 200);
    });
}

// country map
function drawRegionsMap() {

    $.get(country_url, function(data, status) {

        if(data.is_auth_user == false) {
            PageElements.hideTopPanelLoader();
            $('#world_map').html('<p>Please login to view full report.</p>');
        } else {

            if (data.status == 200 && data.country_stats && !jQuery.isEmptyObject(data.country_stats)) {
                country_data.push(['Country', 'Percent of audience']);

                // total number of people
                var total_people = 0;
                for (var key in data.country_stats) {
                    if (data.country_stats.hasOwnProperty(key)) {
                        if (!isNaN(data.country_stats[key]))
                            total_people += parseInt(data.country_stats[key]);
                    }
                }

                for (var key in data.country_stats) {
                    if (data.country_stats.hasOwnProperty(key)) {
                        var tmp_row = [];

                        if (key === 'UK')
                            tmp_row.push('GB');
                        else
                            tmp_row.push(key);
                        if (key === 'US')
                            var percent = parseInt(data.country_stats[key]) / total_people * 100 + 3;
                        else
                            var percent = parseInt(data.country_stats[key]) / total_people * 100;
                        tmp_row.push(Math.round(percent * 100 / 100));
                        country_data.push(tmp_row);
                    }
                }

                var data = google.visualization.arrayToDataTable(country_data);
                var options = {};

                var chart = new google.visualization.GeoChart(document.getElementById('world_map'));

                chart.draw(data, options);

            } else {
                
                if(is_logged_in) {
                    $('#world_map').html('<p>Data not available for this influencer.</p>');
                } else {
                    $('#world_map').html('<p>Please login to view this data.</p>');
                }

                $('#world_map').css('height', '100%');
            }
        }

        PageElements.showMiddlePanel();
        makeTrendsChart();
    }).done(function() {
        PageElements.hideMiddlePanelLoader();
    });
}

function makeTrendsChart() {

    var trends_url = null;
    if(ig_trends_url) {
        trends_url = ig_trends_url;
    } else {
        trends_url = tw_trends_url;
    }

    $.get(trends_url, function(data, status) {

        if(data.is_auth_user == false) {
            $('#bottomPanel').html('<p>Please login to view full report.</p>');
        } else {
            if(data.status == 200 && data.trends_headers && data.trends_values) {

                var monthNames = ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ];

                // make trends chart data
                for(var i = 0; i < data.trends_headers.length; i++) {
                    // convert timestamp to string
                    var newDate = new Date(data.trends_headers[i] / 1000000);

                    if(i % 2 == 0) {
                        continue;
                    }

                    trends_x_axis.push(newDate);
                }
                trends_x_axis.unshift('x');

                var ndx = 0;
                for(var key in data.trends_values) {
                    if(data.trends_values.hasOwnProperty(key)) {
                        trends_cols.push([key]);
                        for (var key2 in data.trends_values[key]) {
                            if(ndx % 2 != 0) {
                                trends_cols[trends_cols.length-1].push(data.trends_values[key][key2]);
                            }
                            ndx++;
                        }

                        ndx = 0;
                    }
                }

                trends_cols.unshift(trends_x_axis);

                // make trends chart
                var chart = c3.generate({
                    bindto: '#trends_chart',
                    data: {
                        x: 'x',
                        columns: trends_cols,
                    },
                    axis: {
                        x: {
                            type: 'timeseries',
                            tick: {
                                count: 5,
                                format: '%Y'
                            },
                            padding: {left: 800},
                            show: true
                        }
                    },
                    padding: {
                        right: 10
                    }
                });
            } else {
                $('#bottomPanel').html('Could not display interest over time.');
            }
        }


        PageElements.showBottomPanel();

    }).done(function() {
        PageElements.hideBottomPanelLoader();
    });
}

var PageElements = {

    init: function() {
        // niches tags input
        $('#id_niches').tagsInput(); // ig
        // prevent right click image
        $('.user_img').bind('contextmenu', function(e) {
            return false;
        }); 

    },

    /**
        Loaders
    **/
    showMainLoader: function() {
        htmlElem.addClass('loading');
        $('#loader-background').css('display', 'block');
    },
    hideMainLoader: function() {
        htmlElem.removeClass('loading');
        $('#loader-background').css('display', 'none');
    },
    showTopPanelLoader: function() {
        $('#audienceStatisticsSpinner').html('<i class="fa fa-refresh fa-spin fa-fw"></i>');
    },
    hideTopPanelLoader: function() {
        $('#audienceStatisticsSpinner').html('');
    },
    showMiddlePanelLoader: function() {
        $('#geographicDistributionSpinner').html('<i class="fa fa-refresh fa-spin fa-fw"></i>');
    },
    hideMiddlePanelLoader: function() {
        $('#geographicDistributionSpinner').html('');
    },
    showBottomPanelLoader: function() {
        $('#interestSpinner').html('<i class="fa fa-refresh fa-spin fa-fw"></i>');
    },
    hideBottomPanelLoader: function() {
        $('#interestSpinner').html('');
    },

    /**
        Show/hide panel
    */
    hideTopPanel: function() {
        $('.chart-col').css('opacity', 0);
        $('#topPanel + .mssg').html('Loading...');
    },
    showTopPanel: function() {
        $('.chart-col').css('opacity', 100);
        $('#topPanel + .mssg').html('');
    },
    hideMiddlePanel: function() {
        $('#middlePanel + .mssg').html('Loading...');
    },
    showMiddlePanel: function() {
        $('#middlePanel + .mssg').html('');
        $('#middlePanel').css('display', 'block');
    },
    hideBottomPanel: function() {
        $('#bottomPanel + .mssg').html('Loading...');
    },
    showBottomPanel: function() {
        $('#bottomPanel + .mssg').html('');
    }
};

function main() {

    PageElements.init();

    // if profile is an instagram user, then start the ajax chain calls
    if(has_ig_account && has_ig_account !== 'False') {
        PageElements.showTopPanelLoader();
        PageElements.showMiddlePanelLoader();
        PageElements.showBottomPanelLoader();
        PageElements.hideTopPanel();
        PageElements.hideMiddlePanel();
        PageElements.hideBottomPanel();

        getProfilePic();
    } 
    // otherwise, let the user know that this is not an instagram user, and then try to display
    // the trends chart
    else {
        $('#world_map').css('height', '100%');

        // twitter users do not have 'Audience statistics' and 'Audience geographic distribution'
        // rows, so display a friendly message to indicate this instead
        $('.chart-row').html('<p>These statistics are not available for twitter users</p>');

        function invalid_array(my_arr){
            for(var i=0; i < my_arr.length; i++){
               if(my_arr[i] === "")   
                  return false;
            }
            return true;
        }

        // check to see if they have hashtags to load
        if(!(niches.split(',').length <= 0 && invalid_array(niches.split(',')))) {

            // show loader for some time and then start retrieving data
            PageElements.showBottomPanelLoader();
            PageElements.hideBottomPanel();
            makeTrendsChart();
        }
    }
}

main();

})();