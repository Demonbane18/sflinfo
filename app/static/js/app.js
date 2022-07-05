$(document).ready(function () {
    $('#loadMe').modal({
    backdrop: 'static',
    keyboard: false
    });

    $('#farm_cryptoassets').DataTable({
                                "order": [[0, "desc"]],
                                "paging": false,
                                "info": false,
                                "searching": false,
                                "stripeClasses": ['odd-row', 'even-row'],
                                "columnDefs": [
                                    {type: "natural-nohtml", targets: 0}
                                ]
                            });
    $('#opensea_cryptoassets').DataTable({
                            "order": [[0, "desc"]],
                            "paging": false,
                            "info": false,
                            "searching": false,
                            "stripeClasses": ['odd-row', 'even-row'],
                            "columnDefs": [
                                {type: "natural-nohtml", targets: 0}
                            ]
                        });
    $('#activity_internal').DataTable({
                            "order": [[0, "desc"]],
                            "paging": true,
                            "info": true,
                            "searching": true,
                            "pageLength" : 10,
                            "stripeClasses": ['odd-row', 'even-row'],
                            "columnDefs": [
                                {type: "natural-nohtml", targets: 0}
                            ]
                        });

    $('#activity_mint').DataTable({
                        "order": [[0, "desc"]],
                        "paging": true,
                        "info": true,
                        "searching": true,
                        "pageLength" : 10,
                        "stripeClasses": ['odd-row', 'even-row'],
                        "columnDefs": [
                            {type: "natural-nohtml", targets: 0}
                        ]
                    });
    $('#activity_burn').DataTable({
                    "order": [[0, "desc"]],
                    "paging": true,
                    "info": true,
                    "searching": true,
                    "pageLength" : 10,
                    "stripeClasses": ['odd-row', 'even-row'],
                    "columnDefs": [
                        {type: "natural-nohtml", targets: 0}
                    ]
                });
    $('#activity_external').DataTable({
                "order": [[0, "desc"]],
                "paging": true,
                "info": true,
                "searching": true,
                "pageLength" : 10,
                "stripeClasses": ['odd-row', 'even-row'],
                "columnDefs": [
                    {type: "natural-nohtml", targets: 0}
                ]
            });
    $('#farmerinfo_totals').DataTable({
            "order": [[0, "desc"]],
            "paging": true,
            "info": true,
            "searching": true,
            "pageLength" : 10,
            "stripeClasses": ['odd-row', 'even-row'],
            "columnDefs": [
                {type: "natural-nohtml", targets: 0}
            ]
        });


    $( "#query_form" ).submit(function( event ) {
        $("#loadMe").removeClass('hidden');
        $('#loadMe').modal('show');
    });
});
