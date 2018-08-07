(function() {

var accountsDiv = $('#accounts');
var htmlElem = $('html');
var page_info = {};

/******************************************/
//  PAGE ELEMENTS
/******************************************/
var PageElements = {

    init: function() {
        // instantiate obfuscation
        let x = baffle('.starred', {
            characters: '⠠ ⠡ ⠢ ⠣ ⠤ ⠥ ⠦ ⠧ ⠨ ⠩ ⠪'
        });
        x.once();

        this.initTagsInput();
    },

    initTagsInput: function() {
        // niches tags input for Instagram
        $('#id_niches').tagsInput({
            autocomplete_url: auto_complete_url,
            autocomplete: {selectFirst:true, width:'100px', autoFill:true}
        });

        // niches tags input for Twitter
        $('#id_tw_niches').tagsInput({
            autocomplete_url: auto_complete_url,
            autocomplete: {selectFirst:true, width:'100px', autoFill:true}
        });
    },

    showLoader: function() {
        htmlElem.addClass('loading');
        $('#loader-background').css('display', 'block');
    },

    removeLoader: function() {
        htmlElem.removeClass('loading');
        $('#loader-background').css('display', 'none');
    }
};

/******************************************/
//  Handles AJAX calls for the panel table
/******************************************/
var DataTableAJAXElement = {

	init: function() {
		window.loadDataTable = this.loadDataTable;
		window.loadDataTableCustom = this.loadDataTableCustom;
	},

    loadDataTable: function(network, additional_params) {
        var load_url;
        if (network === 'ig')
            load_url = main_accounts_page_ig_url;
        else
            load_url = main_accounts_page_tw_url;

        load_url += '?page=1';

        if (additional_params)
            load_url += additional_params;

        PageElements.showLoader();
        accountsDiv.load(load_url, function() {
            TableElement.show();
            PageElements.removeLoader();
        });
    },

    loadDataTableCustom: function(network, additional_params, custom_page, exclude_unverified) {

        var load_url;
        if (network === 'tw')
            load_url = main_accounts_page_tw_url;
        else
            load_url = main_accounts_page_ig_url;

        if (custom_page) {
            load_url += '?page=1';
        } else {
            load_url += '?page=' + page_info.page;
        }

        load_url = load_url.concat('&network=' + page_info.network +
            '&niches=' + page_info.niches + '&min_followers=' + page_info.min_followers +
            '&max_followers=' + page_info.max_followers + '&min_cpm=' + page_info.min_cpm +
            '&min_engagement=' + page_info.min_engagement + '&max_engagement=' + page_info.max_engagement);

        var include_unverified = page_info.unverified_checked;
        if (include_unverified && include_unverified !== '0') {
            load_url += '&unverified=true'
        }

        var include_sort_options = page_info.order_by;
        if (include_sort_options) {
            load_url += '&order_by=' + page_info.order_by;
        } else {
            load_url += '&order_by=followers_reverse';   
        }

        if (additional_params) {
            load_url += additional_params;
        }

        PageElements.showLoader();
        accountsDiv.load(load_url, function() {
            TableElement.show();
            PageElements.removeLoader();
        });
    },

};

/******************************************/
//  Page history -- handle search history
/******************************************/
var PageHistory = {

    init: function() {
        // Make these functions available to the global scope
        window.getSearchHistoryByKey = this.getSearchHistoryByKey;
        window.setSearchHistoryByKey = this.setSearchHistoryByKey;
    },

    historyExists: function() {
        return has_prev && has_prev !== 'None' &&
            has_prev !== 'null';
    },

    updatePageHistory: function() {
        var page = this.getSearchHistoryByKey('sob_page');
        var network = this.getSearchHistoryByKey('sob_network');
        var niches = this.getSearchHistoryByKey('sob_niches');
        var min_followers = this.getSearchHistoryByKey('sob_min_followers');
        var max_followers = this.getSearchHistoryByKey('sob_max_followers');
        var min_cpm = this.getSearchHistoryByKey('sob_min_cpm');
        var max_cpm = this.getSearchHistoryByKey('sob_max_cpm');
        var unverified_checked = this.getSearchHistoryByKey('sob_unverified_checked');
        var order_by = this.getSearchHistoryByKey('sob_order_by');
        var min_engagement = this.getSearchHistoryByKey('sob_min_engagement');
        var max_engagement = this.getSearchHistoryByKey('sob_max_engagement');

        if (page == null)
            page = '1';
        if (network == null)
            network = '';
        if (niches == null)
            niches = '';
        if (min_followers == null)
            min_followers = '';
        if (max_followers == null)
            max_followers = '';
        if (min_cpm == null)
            min_cpm = '';
        if (max_cpm == null)
            max_cpm == '';
        if (order_by == null || order_by === 'None')
            order_by = '';
        if (min_engagement == null)
            min_engagement = '';
        if (max_engagement == null)
            max_engagement = '';

        page_info.page = page;
        page_info.network = network;
        page_info.niches = niches;
        page_info.min_followers = min_followers;
        page_info.max_followers = max_followers;
        page_info.min_cpm = min_cpm;
        page_info.max_cpm = max_cpm;
        page_info.unverified_checked = unverified_checked;
        page_info.order_by = order_by;
        page_info.min_engagement = min_engagement;
        page_info.max_engagement = max_engagement;
    },

    resetPageHistory: function() {
        page_info.page = '1';
        page_info.network = '';
        page_info.niches = '';
        page_info.min_followers = '';
        page_info.max_followers = '';
        page_info.min_cpm = '';
        page_info.max_cpm = '';
        page_info.unverified_checked = '';
        page_info.order_by = '';
        page_info.min_engagement = '';
        page_info.max_engagement = '';
    },

    getSearchHistoryByKey: function(key) {
        return getCookie(key);
    },
    setSearchHistoryByKey: function(key, value) {
        return setCookie(key, value, 1);
    },
};

/******************************************/
//  Search form (IG & TW)
/******************************************/
var SearchFormElement = {

    init: function() {
        window.unconfirmedIsChecked = this.unconfirmedIsChecked;
    },

    unconfirmedIsChecked: function(network) {
        if(network === 'ig') {
            return ($('#ig-checkbox').length > 0 && $('#ig-checkbox').get(0).checked);
        } else if(network === 'tw') {
            return ($('#tw-checkbox').length > 0 && $('#tw-checkbox').get(0).checked);
        }
    },

    setUnConfirmed: function(network, new_val) {
        if(network === 'ig') {
            onDomIsRendered("#ig-checkbox").then(function(element) {
                $('#ig-checkbox').get(0).checked = new_val;
            });
        } else if(network === 'tw') {
            onDomIsRendered("#tw-checkbox").then(function(element) {
                $('#tw-checkbox').get(0).checked = new_val;
            });
        }
    },

    resetFormErrors: function() {
        // remove alert
        document.getElementById('searchFormErrors').className = '';
        document.getElementById('searchFormErrors').innerHTML = '';
    },

    private_make_custom_form: function(network) {

        // if searching tw users, expand twitter tab
        var num_placed = 0;
        if (network === 'tw') {
            if (page_info.min_followers && !isNaN(page_info.min_followers)) {
                $('#id_tw_min_followers').val(parseInt(page_info.min_followers));
                num_placed += 1;
            }
            if (page_info.max_followers && !isNaN(page_info.max_followers)) {
                $('#id_tw_max_followers').val(parseInt(page_info.max_followers));
                num_placed += 1;
            }
            if (page_info.min_cpm && !isNaN(page_info.min_cpm)) {
                $('#id_tw_min_cpm').val(parseFloat(page_info.min_cpm));
                num_placed += 1;
            }
            if (page_info.max_cpm && !isNaN(page_info.max_cpm)) {
                $('#id_tw_max_cpm').val(parseFloat(page_info.max_cpm));
                num_placed += 1;
            }
        } else {
            // set search form
            if (page_info.min_followers && !isNaN(page_info.min_followers)) {
                $('#id_min_followers').val(parseInt(page_info.min_followers));
                num_placed += 1;
            }
            if (page_info.max_followers && !isNaN(page_info.max_followers)) {
                $('#id_max_followers').val(parseInt(page_info.max_followers));
                num_placed += 1;
            }
            if (page_info.min_cpm && !isNaN(page_info.min_cpm)) {
                $('#id_min_cpm').val(parseFloat(page_info.min_cpm));
                num_placed += 1;
            }
            if (page_info.max_cpm && !isNaN(page_info.max_cpm)) {
                $('#id_max_cpm').val(parseFloat(page_info.max_cpm));
                num_placed += 1;
            }
            if (page_info.min_engagement && !isNaN(page_info.min_engagement)) {
                $('#id_min_engagement').val(parseFloat(page_info.min_engagement));
                num_placed += 1;
            }
            if (page_info.max_engagement && !isNaN(page_info.max_engagement)) {
                $('#id_max_engagement').val(parseFloat(page_info.max_engagement));
                num_placed += 1;
            }
        }

        if (num_placed > 0) {
            $('.collapse').collapse('show');
        }

        // now add back niches
        if (page_info.niches) {
            var niches_arr = page_info.niches.split(',');
            for (var i = 0; i < niches_arr.length; ++i) {

                if (page_info.network == 'ig') {
                    $('#id_niches').addTag(niches_arr[i]);
                } else {
                    $('#id_tw_niches').addTag(niches_arr[i]);
                }
            }
        }

        // now update checkboxes
        if (page_info.unverified_checked &&
            page_info.unverified_checked !== '0') {
            if (network == 'ig') {
                SearchFormElement.setUnConfirmed('ig', true);
            } else if (network == 'tw') {
                SearchFormElement.setUnConfirmed('tw', true);
            }
        } else {
            if(network == 'ig') {
                SearchFormElement.setUnConfirmed('ig', false);
            } else if (network == 'tw') {
                SearchFormElement.setUnConfirmed('tw', false);
            }
        }
    },

    newCustomForm: function() {
        var self = this;
        PageHistory.updatePageHistory();

        var network = PageHistory.getSearchHistoryByKey('sob_network');
        if (network === 'tw') {
            $('#twitter_tab a').click();
            self.private_make_custom_form(network);
        } else {
            if (sorter_params) {
                DataTableAJAXElement.loadDataTableCustom(network, sorter_params);
            } else {
                DataTableAJAXElement.loadDataTableCustom(network);
            }
            self.private_make_custom_form(network);
        }
    },

    validateIgSearchForm: function() {

        var min_followers = document.getElementById('id_min_followers').value;
        var max_followers = document.getElementById('id_max_followers').value;
        var min_cpm = document.getElementById('id_min_cpm').value;
        var max_cpm = document.getElementById('id_max_cpm').value;
        var min_engagement = document.getElementById('id_min_engagement').value;
        var max_engagement = document.getElementById('id_max_engagement').value;

        if (min_followers || max_followers) {
            if (!min_followers || !max_followers) {
                document.getElementById('searchFormErrors').className = 'alert alert-danger';
                document.getElementById('searchFormErrors').innerHTML = "<i class=\"fa fa-exclamation-triangle\"" +
                    "aria-hidden=\"true\"></i>&ensp;Min and max followers fields are both required.<br/>";
                return false;
            }
        }

        if (min_cpm || max_cpm) {
            if (!min_cpm || !max_cpm) {
                document.getElementById('searchFormErrors').className = 'alert alert-danger';
                document.getElementById('searchFormErrors').innerHTML = "<i class=\"fa fa-exclamation-triangle\"" +
                    "aria-hidden=\"true\"></i>&ensp;Min and max CPM fields are both required.<br/>";
                return false;
            }
        }

        if (min_engagement || max_engagement) {
            if (!min_engagement || !max_engagement) {
                document.getElementById('searchFormErrors').className = 'alert alert-danger';
                document.getElementById('searchFormErrors').innerHTML = "<i class=\"fa fa-exclamation-triangle\"" +
                    "aria-hidden=\"true\"></i>&ensp;Min and max engagement fields are both required.<br/>";
                return false;
            }
        }

        this.resetFormErrors();
        return true;
    },

    validateTwSearchForm: function() {
        var min_followers = document.getElementById('id_tw_min_followers').value;
        var max_followers = document.getElementById('id_tw_max_followers').value;
        var min_cpm = document.getElementById('id_tw_min_cpm').value;
        var max_cpm = document.getElementById('id_tw_max_cpm').value;

        if (min_followers || max_followers) {
            if (!min_followers || !max_followers) {
                document.getElementById('searchFormErrors').className = 'alert alert-danger';
                document.getElementById('searchFormErrors').innerHTML = "<i class=\"fa fa-exclamation-triangle\"" +
                    "aria-hidden=\"true\"></i>&ensp;Min and max followers fields are both required.<br/>";
                return false;
            }
        }

        if (min_cpm || max_cpm) {
            if (!min_cpm || !max_cpm) {
                document.getElementById('searchFormErrors').className = 'alert alert-danger';
                document.getElementById('searchFormErrors').innerHTML = "<i class=\"fa fa-exclamation-triangle\"" +
                    "aria-hidden=\"true\"></i>&ensp;Min and max CPM fields are both required.<br/>";
                return false;
            }
        }

        this.resetFormErrors();
        return true;
    },

    validateSearchForm: function(network) {
        if(network === 'ig') {
            return this.validateIgSearchForm();
        } else if(network === 'tw') {
            return this.validateTwSearchForm();
        }
    },

    addNichesNotAccountedFor: function() {
        var all_niches = $('.ui-autocomplete-input');
        for(let i = 0; i < all_niches.length; ++i) {
            if(all_niches[i].value !== 'add a niche') {
                if($('#ig_tab').hasClass('active')) {
                    $('#id_niches').addTag(all_niches[i].value);
                } else if($('#twitter_tab').hasClass('active')) {
                    $('#id_tw_niches').addTag(all_niches[i].value);
                }
            }
        } 
    },

    removeNiches: function(network) {

        if(network === 'ig') {
            // TODO
        } else if(network === 'tw') {
            // TODO
        }
    },

    bindUIActions: function() {

        var self = this;

        // start search-btn onclick
        $('.search-btn').on('click', function(event) {
            event.preventDefault();
            self.submitSearch($(this));
        });
        // end search-btn onclick

        // start enter button press
        document.getElementById('id_niches_tag').onkeydown = function(e) {
            console.log(e.keyCode);
            if(e.keyCode == 13) {
                self.submitSearch($('#igSearchBtn'));
            }
        };
        document.getElementById('id_tw_niches_tag').onkeydown = function(e) {
            console.log(e.keyCode);
            if(e.keyCode == 13) {
                self.submitSearch($('#twSearchBtn'));
            }
        };
        // end enter button press
    },

    submitSearch: function(eventSource) {
        var ntwk = eventSource.data('network');

        if (!this.validateSearchForm(ntwk)) {
            event.preventDefault();
            return;
        }

        var url, btn, form, params;
        htmlElem.addClass('loading');
        btn = eventSource;
        url = btn.attr('data-url');
        form = btn.closest('form');

        // add niches that the user typed but hasn't been
        // registered by the tags input plugin yet
        this.addNichesNotAccountedFor();

        var niches = min_followers = max_followers = '';
        var min_cpm = max_cpm = min_engagement = max_engagement = '';

        // use [indexOf] instead of [includes] for IE 11 compatibility
        if (url.indexOf('ig') >= 0) {

            niches = $('#id_niches')[0].value;
            min_followers = $('#id_min_followers')[0].value;
            max_followers = $('#id_max_followers')[0].value;
            min_cpm = $('#id_min_cpm')[0].value;
            max_cpm = $('#id_max_cpm')[0].value;
            min_engagement = $('#id_min_engagement')[0].value;
            max_engagement = $('#id_max_engagement')[0].value;
            url += '&' + 'niches=' + niches + '&min_followers=' +
                min_followers + '&max_followers=' + max_followers +
                '&min_cpm=' + min_cpm + '&max_cpm=' + max_cpm +
                '&min_engagement=' + min_engagement + 
                '&max_engagement=' + max_engagement;
        } else {
            
            niches = $('#id_tw_niches')[0].value;
            min_followers = $('#id_tw_min_followers')[0].value;
            max_followers = $('#id_tw_max_followers')[0].value;
            min_cpm = $('#id_tw_min_cpm')[0].value;
            max_cpm = $('#id_tw_max_cpm')[0].value;
            url += '&' + 'niches=' + niches + '&min_followers=' +
                min_followers + '&max_followers=' + max_followers +
                '&min_cpm=' + min_cpm + '&max_cpm=' + max_cpm;
        }

        var ig_unconfirmed_checked = $('#ig_tab').hasClass('active') && SearchFormElement.unconfirmedIsChecked('ig');
        var tw_unconfirmed_checked = $('#twitter_tab').hasClass('active') && SearchFormElement.unconfirmedIsChecked('tw');
        // toggle unconfirmed
        if (ig_unconfirmed_checked) {
            url += '&unverified=True';
        }
        if (tw_unconfirmed_checked) {
            url += '&unverified=True';
        }

        // toggle default sorting
        url += '&order_by=followers_reverse';

        $('#loader-background').css('display', 'block');
        accountsDiv.load(url, function() {
            TableElement.show();
            PageElements.removeLoader();
            // reset page search history
            PageHistory.resetPageHistory();
        });
    }
};

/******************************************/
// TABLE ELEMENT  
/******************************************/
var TableElement = {

    bindUIActions: function() {

        var self = this;

        $('.x-tab-twitter').on('click', function() {
            SearchFormElement.resetFormErrors();

            if(has_prev && has_prev !== 'None') {

                // reset page history
                PageHistory.resetPageHistory();

                loadDataTableCustom('tw');
                if (!SearchFormElement.unconfirmedIsChecked('tw')) {
                    SearchFormElement.setUnConfirmed('tw', true);
                }
            } else {
                loadDataTable('tw', '&order_by=followers_reverse&unverified=true');
                SearchFormElement.setUnConfirmed('tw', true);
            }

            // remove all lingering niches
            onDomIsRendered("#id_tw_niches").then(function(element) {
                SearchFormElement.removeNiches('tw');
            });
        });

        $('.x-tab-ig').on('click', function() {

            // reset page history
            PageHistory.resetPageHistory();

            SearchFormElement.resetFormErrors();
            loadDataTable('ig', '&order_by=followers_reverse&unverified=true');
            if (SearchFormElement.unconfirmedIsChecked('ig')) {
                SearchFormElement.setUnConfirmed('ig', true);
            }

            // remove all lingering niches
            SearchFormElement.removeNiches('ig');
        });

        accountsDiv.on('mouseover', '.account-entry', function() {
            $(this).addClass('active');
        });

        accountsDiv.on('mouseout', '.account-entry', function() {
            $(this).removeClass('active');
        });

        accountsDiv.on('click', 'a.page', function(event) {

            var url;
            event.preventDefault();

            PageElements.showLoader();

            url = $(this).attr('href');
            if (url !== '#') {
                $('#accounts').load(url, function() {
                    self.show();
                    PageElements.removeLoader();
                    document.getElementById('accountsSearchForm').scrollIntoView();
                });
            }
        });

    },

    show: function() {
        $('.table-responsive').fadeIn(300);
    },
    hide: function() {
        $('.table-responsive').fadeOut(300);
    }
};

function main() {
    PageElements.init();
    DataTableAJAXElement.init();
    PageHistory.init();
    SearchFormElement.init();

    TableElement.bindUIActions();
    SearchFormElement.bindUIActions();

    if (PageHistory.historyExists()) {
        // load homepage with custom search settings
        SearchFormElement.newCustomForm();
    } else {
        // load default homepage with no search settings
        DataTableAJAXElement.loadDataTable('ig', '&order_by=confirmed_reverse&unverified=true');
    }
}
main();


})();