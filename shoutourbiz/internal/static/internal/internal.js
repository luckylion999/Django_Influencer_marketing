(function() {

    var htmlElem = $('html');

    var PageElement = {
        init: function() {

            // instantiate obfuscation
            let x = baffle('.starred', {
                characters: '⠠ ⠡ ⠢ ⠣ ⠤ ⠥ ⠦ ⠧ ⠨ ⠩ ⠪'
            });
            x.once();

            // niches tags input for Instagram
            $('#id_niches').tagsInput({
                autocomplete: {
                    selectFirst: true,
                    width: '100px',
                    autoFill: true
                }
            });

            $('#loader-background').css('z-index', '100000');

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

    var DeleteAccountElement = {
        bindUIActions: function() {
            var self = this;
            $('#deleteAccBtnSubmit').on('click', function(event) {
                event.preventDefault();
                self.deleteThisAccount();
            });
        },

        deleteThisAccount: function() {

            PageElement.showLoader();

            var network = $('#delete_network').val();
            var unconfirmed_id = $('#delete_unconfirmed_id').val();

            $.ajax({
                method: "POST",
                url: delete_url,
                data: {
                    unconfirmed_id: unconfirmed_id,
                    network: network,
                    csrfmiddlewaretoken: csrf,
                },
            }).done(function(data) {
                // now change the modal to display result message
                $('#deleteAccModal .modal-body').html(data);
                $('#deleteAccModal .modal-title').html('Operation completed');
                $('#deleteAccBtnSubmit').css('display', 'none');
                PageElement.removeLoader();
            });
        }
    };

    function main() {
        PageElement.init();
        DeleteAccountElement.bindUIActions();
    }
    main();

})();