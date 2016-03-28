require([
], function() {
  var person;

  function renderBar(p, id) {
    var bar = $('#'+id),
        width = bar.width();
    bar.find('.bar-inner').width(p * width);
  }

  function castVote(vote) {
    $.ajax({
      type: "POST",
      url: "/vote",
      data: JSON.stringify({
        vote: vote
      }),
      contentType: "application/json",
      success: function(data, textStatus, jqXHR) {
        console.log("vote successfully cast");
        setTimeout(function() {
          $('main').empty().html(renderTemplate('voted'));
        }, 2000);
      }
    });
  }

  function makeProposal(proposal) {
    $.ajax({
      type: "POST",
      url: "/propose",
      data: JSON.stringify({
        proposal: proposal
      }),
      contentType: "application/json",
      success: function(data, textStatus, jqXHR) {
        console.log("proposal successfully made");
        console.log(proposal);
      }
    });
  }

  function timeout(time, callback) {
    var fps = 30,
        timeout = 10,
        totalTime = timeout * fps;
        time = totalTime;
        updateInterval = setInterval(function() {
          time--;
          renderBar(time/totalTime, 'time');
          if (time <= 0) {
            callback();
            clearInterval(updateInterval);
          }
        }, 1/fps * 1000);
    return updateInterval;
  }

  function startProposal(proposals) {
    $("main").empty().html(renderTemplate('propose', {proposals: proposals}));
    var updateInterval = timeout(10, function() {
      makeProposal(null);
    });
    $('.proposal').empty().html(renderTemplate('proposal', proposals[0]));
    $('button').on('click', function() {
      var proposal = {
        type: $('[name=type]').val(),
        target: $('[name=target]').val(),
        value: $('[name=value]').val()
      };
      makeProposal(proposal);
      clearInterval(updateInterval);
    });
    $('.proposals').on('change', function() {
      var proposalType = $(this).val(),
          proposal = _.find(proposals, function(p) { return p.type == proposalType });
      console.log('changed proposal to');
      console.log(proposalType);
      console.log(proposal);
      console.log(proposals);
      $('.proposal').empty().html(renderTemplate('proposal', proposal));
    });
  }

  function startVote(proposal) {
    $("main").empty().html(renderTemplate('vote', proposal));
    var updateInterval = timeout(10, function() {
      castVote(null);
    });
    $('button').on('click', function() {
      var val = $(this).val();
      castVote(val);
      clearInterval(updateInterval);
    });
  }

  function showPerson() {
    $("main").empty().html(renderTemplate('person', person));
  }

  $(function() {
    var socket = io('/player');
    socket.on('propose', function(data) {
      startProposal(data.proposals);
    });

    socket.on('vote', function(data) {
      console.log('voting on:');
      console.log(data);
      startVote(data.proposal);
    });

    socket.on('person', function(data) {
      person = data;
      showPerson();
    });
  });
});
