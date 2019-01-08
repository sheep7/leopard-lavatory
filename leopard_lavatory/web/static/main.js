
function refreshMap() {
    var mf = document.getElementById("mapframe");
    var address = document.getElementById("addressinput").value;
    mf.src = "https://kartor.stockholm.se"
           + "/bios/dpwebmap/cust_sth/sbk/sthlm_sse/DPWebMap.html?"
           + "zoom=7&layers=TTTB000000000T&super_search=" + address;
}

new autoComplete({
    selector: '#addressinput',
    minChars: 1,
    source: function(term, suggest){
        term = term.toLowerCase();
        var choices = [['Torsgatan 7', 'g'], ['Testfastighet 7', 'f'], ['Testgatan 1', 'g']];
        var suggestions = [];
        for (i=0;i<choices.length;i++)
            if (~(choices[i][0]+' '+choices[i][1]).toLowerCase().indexOf(term))
                suggestions.push(choices[i]);
        suggest(suggestions);
    },
    renderItem: function (item, search){
        search = search.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
        var re = new RegExp("(" + search.split(' ').join('|') + ")", "gi");
        return '<div class="autocomplete-suggestion" data-addr="'+item[0]+'" data-type="'+item[1]+'" data-val="'+search+'"><img src="static/'+item[1]+'.png"> '+item[0].replace(re, "<b>$1</b>")+'</div>';
    },
    onSelect: function(e, term, item){
        alert('Item "'+item.getAttribute('data-addr')+' ('+item.getAttribute('data-type')+')" selected by '+(e.type == 'keydown' ? 'pressing enter' : 'mouse click')+'.');
    }
});
