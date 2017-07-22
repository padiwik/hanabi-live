// Sent when the user has joined a game and the UI has been initialized
// "data" is empty

// Imports
const globals = require('../globals');
const logger = require('../logger');
const models = require('../models');
const notify = require('../notify');

// When the client has joined a game after they have initialized the UI
exports.step1 = (socket, data) => {
    // Local variables
    data.gameID = socket.currentGame;

    // Check to make sure this table exists
    if (!(data.gameID in globals.currentGames) &&
        socket.status !== 'Replay') { /* eslint-disable padded-blocks */

        logger.warn(`User "${data.username}" tried to ready for game #${data.gameID} with status ${socket.status}, but that game does not exist.`);
        data.reason = 'That game does not exist.';
        notify.playerDenied(socket, data);
        return;
    }

    if (socket.status === 'Replay' || socket.status === 'Shared Replay') {
        models.games.getActions(socket, data, step2);
    } else {
        data.game = globals.currentGames[data.gameID];
        step2(null, socket, data);
    }
};

function step2(error, socket, data) {
    if (error !== null) {
        logger.error('Error: models.games.getActions failed:', error);
        return;
    }

    // This is either from "globals.currentGames" or built by the database
    const game = data.game;

    // Get the index of this player
    let index = -1; // Set an impossible index by default
    if (socket.status !== 'Replay' && socket.status !== 'Shared Replay') {
        // We only have to worry about getting the index if we need to
        // scrub cards
        for (let i = 0; i < game.players.length; i++) {
            if (game.players[i].userID === socket.userID) {
                index = i;
                break;
            }
        }
    }

    // Send a "notify" or "message" message for every game action of the deal
    for (const action of game.actions) {
        // Scrub card info from cards if the card is in their own hand
        let scrubbed = false;
        let scrubbedAction;
        if (action.type === 'draw' && action.who === index) {
            scrubbed = true;
            scrubbedAction = JSON.parse(JSON.stringify(action));
            scrubbedAction.rank = undefined;
            scrubbedAction.suit = undefined;
        }

        socket.emit('message', {
            type: ('text' in action ? 'message' : 'notify'),
            resp: (scrubbed ? scrubbedAction : action),
        });
    }

    // If it is their turn, send an "action" message
    if (game.turn_player_index === index) {
        notify.playerAction(socket, data);
    }

    // Send an "advanced" message
    // (if this is not sent during a replay, the UI will look uninitialized)
    socket.emit('message', {
        type: 'advanced',
    });

    // Send them the number of spectators
    if (socket.status !== 'Replay') {
        socket.emit('message', {
            type: 'num_spec',
            resp: {
                num: Object.keys(globals.currentGames[data.gameID].spectators).length,
                // We can't use "game.spectators" because that property doesn't
                // exist in the "fake" game object
            },
        });
    }

    // Send them the current time for all player's clocks
    if (socket.status !== 'Replay' && socket.status !== 'Shared Replay') {
        const times = [];
        for (let i = 0; i < game.players.length; i++) {
            let time = game.players[i].time;

            // Since we are sending the message in the middle of someone's turn,
            // we need to account for this
            if (game.turn_player_index === i) {
                const currentTime = (new Date()).getTime();
                const elapsedTime = currentTime - game.turn_begin_time;
                time -= elapsedTime;
            }

            times.push(time);
        }
        socket.emit('message', {
            type: 'clock',
            resp: {
                times,
                active: game.turn_player_index,
            },
        });
    }

    // Enable the replay controls for the leader of the review
    if (socket.status === 'Shared Replay' &&
        socket.userID === globals.currentGames[data.gameID].owner) {
        // We can't use "game.owner" because that property doesn't exist in the
        // "fake" game object

        socket.emit('message', {
            type: 'replay_owner',
            resp: {
                owner: true,
            },
        });
    }

    // Send them to the current turn that everyone else is at
    if (socket.status === 'Shared Replay') {
        socket.emit('message', {
            type: 'replay_turn',
            resp: {
                turn: globals.currentGames[data.gameID].turn_num,
            },
        });
    }
}
