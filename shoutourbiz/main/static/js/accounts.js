(function() {

/*********************************************/
//  Badges
/*********************************************/
var BadgesElement = {

    resizeBadges: function() {

        var table_width = document.getElementById('homePanelTable').offsetWidth;
        var v_niches = document.getElementsByClassName('single-line');

        for(var i = 0; i < v_niches.length; ++i) {

            // length of the row
            var current_len = 0;
            var badges = v_niches[i].querySelectorAll('.badge');
            for(var j = 0; j < badges.length; ++j) {

                var badge_width = badges[j].offsetWidth;
                current_len += badge_width;

                if(current_len >= (table_width * 0.20)) {
                    badges[j].style.display = 'none';
                } else {
                    badges[j].style.display = 'inline-block';
                }
            }

            break;

        }
    }
};

/*********************************************/
//  Contains page elements
/*********************************************/
var PageElements = {

    /** 
        Page constructor 
    **/
    init: function() {

        // initialize tooltips
        $('[data-toggle="tooltip"]').tooltip();

        for(var i = 0; i < $('.username-preview').length; ++i) {
            $('.username-preview')[i].textContent = $('.username-preview')[i].textContent.replace(/ /g, '');
        }
        for(var i = 0; i < $('.email-preview').length; ++i) {
            $('.email-preview')[i].textContent = $('.email-preview')[i].textContent.replace(/ /g, '');
        }

        $('#homePanelTableDiv').stickyTableHeaders({
            fixedOffset: $('.navbar'),
            cacheHeaderHeight: true,
        });
    }

};

/*********************************************/
//  CLICK TABLE ENTRY
/*********************************************/
var SearchElement = {

    storeSearchInfo: function() {
        // store current search info so that user can go back to home page
        setSearchHistoryByKey('sob_page', sob_page_number, 1);
        setSearchHistoryByKey('sob_network', sob_network, 1);
        setSearchHistoryByKey('sob_niches', sob_niches, 1);
        setSearchHistoryByKey('sob_min_followers', sob_min_followers, 1);
        setSearchHistoryByKey('sob_max_followers', sob_max_followers, 1);
        setSearchHistoryByKey('sob_min_cpm', sob_min_cpm, 1);
        setSearchHistoryByKey('sob_max_cpm', sob_max_cpm, 1);
        setSearchHistoryByKey('sob_order_by', global_order_by);
        setSearchHistoryByKey('sob_min_engagement', sob_min_engagement, 1);
        setSearchHistoryByKey('sob_max_engagement', sob_max_engagement, 1);

        if(($('#ig_tab').hasClass('active') && unconfirmedIsChecked('ig')) || 
                ($('#twitter_tab').hasClass('active') && unconfirmedIsChecked('tw'))) {
            setSearchHistoryByKey('sob_unverified_checked', 1);
        } else {
            setSearchHistoryByKey('sob_unverified_checked', 0);
        }
    },

    /** 
        Build url based on search form 
    **/
    buildSearchFormUrl: function(network, url) {

        var niches, min_followers, max_followers, min_cpm, max_cpm = '';
        if(network === 'ig') {
            niches = $('#id_niches').val();
            min_followers = $('#id_min_followers').val();
            max_followers = $('#id_max_followers').val();
            min_cpm = $('#id_min_cpm').val();
            max_cpm = $('#id_max_cpm').val();
            min_engagement = $('#id_min_engagement').val();
            max_engagement = $('#id_max_engagement').val();
        } else if(network === 'tw') {
            niches = $('#id_tw_niches').val();
            min_followers = $('#id_tw_min_followers').val();
            max_followers = $('#id_tw_max_followers').val();
            min_cpm = $('#id_tw_min_cpm').val();
            max_cpm = $('#id_tw_max_cpm').val();
            min_engagement = '';
            max_engagement = '';
        }

        url += '&niches=' + niches + '&min_followers=' + min_followers +
            '&max_followers=' + max_followers + '&min_cpm=' + min_cpm +
            '&max_cpm=' + max_cpm + '&min_engagement=' + min_engagement +
            '&max_engagement=' + max_engagement;

        return url;
    },

    /**
        Set header arrows if a previous sorting session exists
    */
    setPreviousSortSession: function(order_by) {
       
        // add arrow to 'id' header
        if(order_by.toLowerCase() === 'id')
            $('#idHeader').append('<span class="arrow">&uarr;</span>');
        else if(order_by.toLowerCase() === 'id_reverse')
            $('#idHeader').append('<span class="arrow">&darr;</span>');
        else if(order_by.toLowerCase() === 'followers')
            $('#followersHeader').append('<span class="arrow">&uarr;</span>');
        else if(order_by.toLowerCase() === 'followers_reverse')
            $('#followersHeader').append('<span class="arrow">&darr;</span>');
        else if(order_by.toLowerCase() === 'cpm')    
            $('#cpmHeader').append('<span class="arrow">&uarr;</span>');
        else if(order_by.toLowerCase() === 'cpm_reverse')   
            $('#cpmHeader').append('<span class="arrow">&darr;</span>');
        else if(order_by.toLowerCase() === 'confirmed')    
            $('#confirmedHeader').append('<span class="arrow">&uarr;</span>');
        else if(order_by.toLowerCase() === 'confirmed_reverse')   
            $('#confirmedHeader').append('<span class="arrow">&darr;</span>');
        else if(order_by.toLowerCase() === 'engagement')   
            $('#engagementHeader').append('<span class="arrow">&uarr;</span>');
        else if(order_by.toLowerCase() === 'engagement_reverse')   
            $('#engagementHeader').append('<span class="arrow">&darr;</span>');

        if(global_order_by && global_order_by !== 'None') {
            sorter_params = '&' + global_order_by;
        }
    }
};

var SorterElement = {

    handleHeaderClick: function(text, parent) {
        // clicked ID header
        if(text.toLowerCase() === 'id') {

            if(global_order_by === 'id') {
                parent.attr('data-direction', 'up');
            } else if(global_order_by === 'id_reverse') {
                parent.attr('data-direction', 'down');
            } 

            if(!parent.attr('data-direction')) {

                parent.attr('data-direction', 'up'); 
                sorter_params = '&order_by=id';
            } 
            else if(parent.attr('data-direction') && 
                    parent.attr('data-direction') == 'up') {

                parent.attr('data-direction', 'down');
                sorter_params = '&order_by=id_reverse';
            }
            else if(parent.attr('data-direction') && 
                    parent.attr('data-direction') == 'down') {

                parent.attr('data-direction', 'up');
                sorter_params = '&order_by=id';
            } 
        }

        // clicked Followers header
        if(text.toLowerCase() === 'followers') {

            if(global_order_by === 'followers') {
                parent.attr('data-direction', 'up');
            } else if(global_order_by === 'followers_reverse') {
                parent.attr('data-direction', 'down');
            } 

            if(!parent.attr('data-direction')) {

                parent.attr('data-direction', 'up'); 
                sorter_params = '&order_by=followers';
            } 
            else if(parent.attr('data-direction') && 
                    parent.attr('data-direction') == 'up') {

                parent.attr('data-direction', 'down');
                sorter_params = '&order_by=followers_reverse';
            }
            else if(parent.attr('data-direction') && 
                    parent.attr('data-direction') == 'down') {

                parent.attr('data-direction', 'up');
                sorter_params = '&order_by=followers';
            } 
        }

        // clicked CPM header
        if(text.toLowerCase() === 'cpm') {

            if(global_order_by === 'cpm') {
                parent.attr('data-direction', 'up');
            } else if(global_order_by === 'cpm_reverse') {
                parent.attr('data-direction', 'down');
            } 

            if(!parent.attr('data-direction')) {

                parent.attr('data-direction', 'up'); 
                sorter_params = '&order_by=cpm';
            } 
            else if(parent.attr('data-direction') && 
                    parent.attr('data-direction') == 'up') {

                parent.attr('data-direction', 'down');
                sorter_params = '&order_by=cpm_reverse';
            }
            else if(parent.attr('data-direction') && 
                    parent.attr('data-direction') == 'down') {

                parent.attr('data-direction', 'up');
                sorter_params = '&order_by=cpm';
            } 
        }

        // clicked Confirmed header
        if(text.toLowerCase() === 'confirmed') {

            if(global_order_by === 'confirmed') {
                parent.attr('data-direction', 'up');
            } else if(global_order_by === 'confirmed_reverse') {
                parent.attr('data-direction', 'down');
            } 

            if(!parent.attr('data-direction')) {

                parent.attr('data-direction', 'up'); 
                sorter_params = '&order_by=confirmed';
            } 
            else if(parent.attr('data-direction') && 
                    parent.attr('data-direction') == 'up') {

                parent.attr('data-direction', 'down');
                sorter_params = '&order_by=confirmed_reverse';
            }
            else if(parent.attr('data-direction') && 
                    parent.attr('data-direction') == 'down') {

                parent.attr('data-direction', 'up');
                sorter_params = '&order_by=confirmed';
            } 
        }

        // clicked Engagement header
        if(text.toLowerCase() === 'engagement') {

            if(global_order_by === 'engagement') {
                parent.attr('data-direction', 'up');
            } else if(global_order_by === 'engagement_reverse') {
                parent.attr('data-direction', 'down');
            } 

            if(!parent.attr('data-direction')) {

                parent.attr('data-direction', 'up'); 
                sorter_params = '&order_by=engagement';
            } 
            else if(parent.attr('data-direction') && 
                    parent.attr('data-direction') == 'up') {

                parent.attr('data-direction', 'down');
                sorter_params = '&order_by=engagement_reverse';
            }
            else if(parent.attr('data-direction') && 
                    parent.attr('data-direction') == 'down') {

                parent.attr('data-direction', 'up');
                sorter_params = '&order_by=engagement';
            } 
        }

        if ($('#tw-checkbox') && $('#tw-checkbox').get(0).checked ||
                $('#ig-checkbox') && $('#ig-checkbox').get(0).checked) {
            sorter_params += '&unverified=True'
        }
    },

    bindUIActions: function() {

        var self = this;

        $('#accounts').on('click', '.account-entry', function() {

            var uid = $(this).attr('data-id');
            var new_profiles_details_url = profile_details_url.replace('0', uid);

            // store search info for current page so that user can get back
            // to search results again
            SearchElement.storeSearchInfo();

            window.location.href = new_profiles_details_url + '?prev=home';
        });


        $('.link-sort-header').on('click', function (event) {

            var text = $(this).text();
            var parent = $(this).parent();
            
            self.handleHeaderClick(text, parent);
            sorter_params = SearchElement.buildSearchFormUrl(network, sorter_params);

            // now load data table
            if(has_prev && has_prev !== 'None') {
                loadDataTableCustom(network, sorter_params, 1);
            } else {
                loadDataTable(network, sorter_params, 1);
            }
        });

    },
};

/**
    Main function. Start here...
*/ 
function main() {
    PageElements.init();
    SearchElement.setPreviousSortSession(global_order_by);
    SorterElement.bindUIActions();
}
main();

})();