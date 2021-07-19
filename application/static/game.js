var me_cards = [];
var me_player;
var card_dealing = 0;

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




//function to handle when a bid is made - disable dropdown and socket emit
$('#bid_submit').click(function(){
    var bid = $('#bid_dropdown').find(":selected").val();
    $('#bid_dropdown').find('option').remove();
    $(this).prop('disabled',true);
    socket.emit('bid_made', {player_order:me_order, game_id:game_id, bid:bid});
});


//function to handle when a card is dealt
$(document).on('click', '[id*="card_"]', function(e){
    card_id = e.target.id;
    if(card_dealing == 1 && $('#'+card_id).css('opacity') == 1){
        card_dealing = 0;
        $('#show_trump').prop('disabled', true);
        $('#me_deck').children().css('opacity',1);
        card_id = card_id.replace("card_", "");
        socket.emit('card_dealt', {game_id: game_id, player_order:me_order, card:card_id});
        $(this).remove();
    }
});


//function to handle when trump is set - disable trump setter and socket emit
$(document).on('click','#trump_submit',function(){
    var trump = $('#trump_dropdown').find(":selected").val();
    var trump_order = $('#trump_order').val();
    $(this).remove();
    $('#trump_dropdown').remove();
    $('#trump_order').remove();
    $('#trump_order_label').remove();
    socket.emit('trump_made', { game_id:game_id, trump:trump, trump_order:trump_order });
});

//function to handle when double is set/not set
$(document).on('click','#yes_double',function(){
    $(this).remove();
    $('#no_double').remove();
    $('#double_text').remove();
    socket.emit('double_made', {player_team:me_team, player_order:me_order, game_id:game_id, double:1});
});
$(document).on('click','#no_double',function(){
    $(this).remove();
    $('#yes_double').remove();
    $('#double_text').remove();
    socket.emit('double_made', {player_team:me_team, player_order:me_order, game_id:game_id, double:0});
});

//function to handle when 24 is bid/not bid
$(document).on('click','#yes_24',function(){
    $(this).remove();
    $('#no_24').remove();
    $('#24_text').remove();
    socket.emit('24_made', {player_order:me_order, game_id:game_id, aukat:1});
});
$(document).on('click','#no_24',function(){
    $(this).remove();
    $('#yes_24').remove();
    $('#24_text').remove();
    socket.emit('24_made', {player_order:me_order, game_id:game_id, aukat:0});
});

//function to handle when trump is revealed
$(document).on('click', '#show_trump', function(){
    $(this).prop('disabled', true);
    socket.emit('trump_revealed', {game_id:game_id, player_order:player_order});
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


//helper function to update game screen
function update_screen(p_order, data, type){
    if(type.localeCompare("image") == 0)
        data = $('<img/>', {src:'static/img/'+data+'.png'}).height('140px').width('100px');
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

//helper functtion to empty screen
function empty_screen(){
    $('#bid').empty();
    $('#me_flex').empty();
    $('#partner_flex').empty();
    $('#left_opponent_flex').empty();
    $('#right_opponent_flex').empty();
}


/**when game needs to be updated -
update screen, status
new_player (new player has joined game) - update new player's info
bid_start (bidding will start now) - show first 4 cards for all players, show bidding dropdown for player with order 0
bid (bid is made) - make the bid dropdown for next player
double (bidding round is complete) - ask for double
set_trump  (trump is to be set) - make the trump dropdown
show_all_cards - show all cards for everyone and ask opponents for 24
**/
socket.on('update_game', function(message){
    if(message.hasOwnProperty('info'))
        info = message['info'];
    gameType = message['type'];
    if(message.hasOwnProperty('screen')){
        screen = message['screen'];
        if(screen.clear == 1)
            empty_screen()
        update_screen(screen.player_order, screen.data, screen.type);
    }
    if(message.hasOwnProperty('status')){
        $('#status').html(message.status);
    }
    if(message.hasOwnProperty('trump')){
        $('#trump').html($('<img/>', {src:'static/img/'+message.trump+'.png'}));
    }

    if(gameType.localeCompare('new_player') == 0){
        if(info.player_id != me_id){
            switch(info.player_order){
                case parseInt($('#partner_info').attr('data-order')):
                    $('#partner_info').html(info.player_name);
                    break;
                case parseInt($('#left_opponent_info').attr('data-order')):
                    $('#left_opponent_info').html(info.player_name);
                    break;
                case parseInt($('#right_opponent_info').attr('data-order')):
                    $('#right_opponent_info').html(info.player_name);
                    break;
            }
        }
    }

    else if(gameType.localeCompare('bid_start') == 0){
        me_cards = [];
        for(var i=0; i < 8; i++){
            me_cards.push(info['player'+String(me_order)].deck[i]);
        }
        $('#me_deck').empty();
        for(var i=0;i<4;i++){
            c = me_cards[i];
            $('#me_deck').append($('<img/>', {
                id: "card_"+c.id,
                src: 'static/img/'+c.name+'_of_'+c.suite+'.png'
            }).height('140px').width('100px').css('opacity',1));
        }
        if(me_order==0)
            make_bid_dropdown(16);
    }

    else if(gameType.localeCompare('bid') == 0){
        if(info.hasOwnProperty('double_set')){
            if(info.double_set == 2)
                $('#game_double').html("Double set");
            else if(info.double_set == 4)
                $('#game_double').html("Re-Double set");
        }
        if(me_order == info.next_player_order)
            make_bid_dropdown(info.data);

    }

    else if(gameType.localeCompare('double') == 0) {
        if(info.hasOwnProperty('bid_winner')){
            $('#game_bid').html("Bid won by "+info.bid_winner+" at "+info.highest_bid);
        }
        if(info.hasOwnProperty('double_set')){
            if(info.double_set == 2)
                $('#game_double').html("Double set");
            else if(info.double_set == 4)
                $('#game_double').html("Re-Double set");
        }
        if(me_order == info.double_player_order){
            $('#bid').append('<br><p id="double_text">Do you want to set double?</p>');
            $('#bid').append($('<button/>', {id:'yes_double', text:'Yes'}));
            $('#bid').append($('<button/>', {id:'no_double', text:'No'}));
        }
    }

    else if(gameType.localeCompare('set_trump') == 0){
        if(info.hasOwnProperty('double_set')){
            if(info.double_set == 2)
                $('#game_double').html("Double set");
            else if(info.double_set == 4)
                $('#game_double').html("Re-Double set");
        }
        if(info.bid_winner_order == me_order){
            var arr = [{val : 0, text: 'Spades'},
                  {val : 1, text: 'Hearts'},
                  {val : 2, text: 'Clubs'},
                  {val : 3, text: 'Diamonds'},
                  {val : 4, text: 'No Trump'}
                ];
            $('#bid').append($('<select/>', {
                id:'trump_dropdown'
            }));
            $(arr).each(function() {
                $('#trump_dropdown').append($('<option/>',
                        {value:this.val, text:this.text}));
            });
            $('#bid').append('<br><input type="checkbox" id="trump_order" /><label for="trump_order" id="trump_order_label">Reverse</label>');
            $('#bid').append($('<button/>', {id:'trump_submit', text:'Set Trump'}));
        }
    }

    else if(gameType.localeCompare('show_all_cards') == 0){
        for(var i=4;i<8;i++){
            c = me_cards[i];
            $('#me_deck').append($('<img/>', {
                id: "card_"+c.id,
                src: 'static/img/'+c.name+'_of_'+c.suite+'.png'
            }).height('140px').width('100px').css('opacity',1));
        }
        if(me_order ==  info.player_24_order){
            $('#bid').append('<br><p id="24_text">Do you want to re-bid 24?</p>');
            $('#bid').append($('<button/>', {id:'yes_24', text:'Yes'}));
            $('#bid').append($('<button/>', {id:'no_24', text:'No'}));
        }
    }

    else if(gameType.localeCompare('ask_for_24') == 0){
        if(me_order ==  info.player_24_order){
            $('#bid').append('<br><p id="24_text">Do you want to re-bid 24?</p>');
            $('#bid').append($('<button/>', {id:'yes_24', text:'Yes'}));
            $('#bid').append($('<button/>', {id:'no_24', text:'No'}));
        }
    }

    else if(gameType.localeCompare('game_start') == 0){
        if(me_order == 0)
            card_dealing = 1;
    }

    else if(gameType.localeCompare('deal_card') == 0){
        if(me_order == info.next_player_order) {
            for(var i in info.restrictions){
                c_id = info.restrictions[i];
                console.log(c_id);
                $('#card_'+c_id).css('opacity', 0.3);
            }
            card_dealing = 1;
            if(info.allow_trump_reveal == 1){
                $('#show_trump').prop('disabled',false);
            }
        }
    }





});

