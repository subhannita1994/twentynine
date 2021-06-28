 var me_cards = [];
var me_player;

//assigning data order
if(me_order < 2){
        $('#partner_info').attr('data-order', me_order+2);
        $('#partner_flex').attr('data-order', me_order+2);
        $('#right_opponent_info').attr('data-order', me_order+1);
        $('#right_opponent_flex').attr('data-order', me_order+1);
        if(me_order == 0){
            $('#left_opponent_info').attr('data-order', 3);
            $('#left_opponent_flex').attr('data-order', 3);
        }
        else{
            $('#left_opponent_info').attr('data-order', 0);
            $('#left_opponent_flex').attr('data-order', 0);
        }
    }
    else{
        $('#partner_info').attr('data-order', me_order-2);
        $('#left_opponent_info').attr('data-order', me_order-1);
        $('#partner_flex').attr('data-order', me_order-2);
        $('#left_opponent_flex').attr('data-order', me_order-1);
        if(me_order == 2){
            $('#right_opponent_info').attr('data-order', 3);
            $('#right_opponent_flex').attr('data-order', 3);
        }
        else{
            $('#right_opponent_info').attr('data-order', 0);
            $('#right_opponent_flex').attr('data-order', 0);
        }
    }



    // on connection, emit back me player
var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
socket.on('connect', function() {
    console.log("connected");
    socket.emit('join', {game_id: game_id, player_id:me_id});
});



//when new player joins, update his place
socket.on('new_player', function(msg){
    if(msg.player_id != me_id){
        switch(msg.player_order){
            case parseInt($('#partner_info').attr('data-order')):
                $('#partner_info').html(msg.player_name);
                break;
            case parseInt($('#left_opponent_info').attr('data-order')):
                $('#left_opponent_info').html(msg.player_name);
                break;
            case parseInt($('#right_opponent_info').attr('data-order')):
                $('#right_opponent_info').html(msg.player_name);
                break;
        }
    }
});


//function to handle when a bid is made - disable dropdown and socket emit
$('#bid_submit').click(function(){
    var bid = $('#bid_dropdown').find(":selected").val();
    $('#bid_dropdown').find('option').remove();
    $(this).prop('disabled',true);
    socket.emit('bid_made', {player_order:me_order, game_id:game_id, bid:bid});
});


//function to handle when a card is dealt
var cardDealt = function(){
    console.log("some card is dealt - don't know what yet");
};

//function to handle when trump is set - disable trump setter and socket emit
$('#trump_submit').click(function(){
    var trump = $('#trump_dropdown').find(":selected").val();
    var trump_order = $('#trump_order').val();
    $(this).remove();
    $('#trump_dropdown').remove();
    $('#trump_order').remove();
    socket.emit('trump_made', { game_id:game_id, trump:trump, trump_order:trump_order });
});

//function to handle when double is set/not set
$('#yes_double').click(function(){
    $(this).remove();
    $('#no_double').remove();
    socket.emit('double_made', {player_team:me_team, player_order:me_order, game_id:game_id, double:1});
});
$('#no_double').click(function(){
    $(this).remove();
    $('#yes_double').remove();
    socket.emit('double_made', {player_team:me_team, player_order:me_order, game_id:game_id, double:0});
});

//function to handle when 24 is bid/not bid
$('#yes_24').click(function(){
    $(this).remove();
    $('#no_24').remove();
    socket.emit('24_made', {player_order:me_order, game_id:game_id, aukat:1});
});
$('#no_24').click(function(){
    $(this).remove();
    $('#yes_24').remove();
    socket.emit('24_made', {player_order:me_order, game_id:game_id, aukat:0});
});


//helper function to make bid dropdown
function make_bid_dropdown(minBid){
    $('#bid_dropdown').find('option').remove();
    $('#bid_dropdown').append($('<option/>', {
            value: -1,
            text: "Pass"
        }));
    for(var i=minBid; i<28; i++){
        $('#bid_dropdown').append($('<option/>', {
            value: i,
            text: i.toString()
        }));
    }
    $('#bid_submit').prop('disabled',false);
}

//when bid has started - show first four cards, show bidding dropdown for player0
socket.on('bid_start', function(msg){
    for(var i=0; i < 8; i++){
        me_cards.push(msg['player'+String(me_order)].deck[i]);
    }
    for(var i=0;i<4;i++){
        c = me_cards[i];
        $('#me_deck').append($('<img/>', {
            id: c.id,
            src: 'static/img/'+c.name+'_of_'+c.suite+'.png',
            click: cardDealt
        }).height('140px').width('100px'));
    }
    if(me_order==0)
        make_bid_dropdown(16);
});

//helper function to update game screen
function update_screen(p_order, data){
    switch(p_order){
            case parseInt($('#me_flex').attr('data-order')):
                $('#me_flex').html(data);
                break;
            case parseInt($('#partner_flex').attr('data-order')):
                $('#partner_flex').html(data);
                break;
            case parseInt($('#left_opponent_flex').attr('data-order')):
                $('#left_opponent_flex').html(data);
                break;
            case parseInt($('#right_opponent_flex').attr('data-order')):
                $('#right_opponent_flex').html(data);
                break;
        }
}

/**when game needs to be updated -
update screen
bid (bid is made) - make the bid dropdown for next player
double (bidding round is complete) - ask for double
set_trump  (trump is to be set) - make the trump dropdown
show_all_cards - show all cards for everyone
ask_for_24 - and ask opponents for 24
**/
socket.on('update_game', function(message){
    if(message.hasOwnProperty('info'))
        info = message['info'];
    gameType = message['type'];
    if(message.hasOwnProperty('screen')){
        screen = message['screen'];
        update_screen(screen.player_order, screen.data);
    }
    if(gameType.localeCompare('bid') == 0){
        if(me_order == info.next_player_order)
            make_bid_dropdown(info.data);

    }else if(gameType.localeCompare('double') == 0) {
        if(me_order == info.double_player_order){
            $('#bid').append('<br><p>Do you want to set double?</p>');
            $('#bid').append($('<button/>', {id:'yes_double', text:'Yes'}));
            $('#bid').append($('<button/>', {id:'no_double', text:'No'}));
        }
    }else if(gameType.localeCompare('set_trump') == 0){
        if(info.bid_winner_order == me_order){
            var arr = [{val : 0, text: 'Spades'},
                  {val : 1, text: 'Hearts'},
                  {val : 2, text: 'Clubs'},
                  {val : 3, text: 'Diamonds'}
                ];
            $('#bid').append($('<select/>', {
                id:'trump_dropdown'
            }));
            $(arr).each(function() {
                $('#trump_dropdown').append($('<option/>',
                        {value:this.val, text:this.text}));
            });
            $('#bid').append('<br><input type="checkbox" id="trump_order" />Reverse<br/>');
            $('#bid').append($('<button/>', {id:'trump_submit', text:'Set Trump'}));
        }
    }else if(gameType.localeCompare('show_all_cards')){
        for(var i=4;i<8;i++){
            c = me_cards[i];
            $('#me_deck').append($('<img/>', {
                id: c.id,
                src: 'static/img/'+c.name+'_of_'+c.suite+'.png',
                click: cardDealt
            }).height('140px').width('100px'));
        }
    }else if(gameType.localeCompare('ask_for_24')){
        if(me_order ==  info.player_24_order){
            $('#bid').append('<br><p>Do you want to re-bid 24?</p>');
            $('#bid').append($('<button/>', {id:'yes_24', text:'Yes'}));
            $('#bid').append($('<button/>', {id:'no_24', text:'No'}));
        }
    }





});

