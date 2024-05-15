$(document).ready(function() {
    $('#user-input').keypress(function(event) {
        if (event.which == 13) {
            sendMessage();
            animateButton();
        }
    });
});

function toggleChat() {
    $('#chat-container').toggle();
    $('.chat-icon').toggle(); // Toggle visibility of chat icon
}

function sendMessage() {
    var message = $('#user-input').val();
    if (message.trim() == '') return;

    // Append user message with user image
    $('#chat-box').append('<div class="message-container user-message-container"><img src="/images/user_image.jpg" alt="User" class="user-image"> <div class="message">' + message + '</div></div>');
    $('#user-input').val('');

    $.ajax({
        type: 'POST',
        url: '/get_response',
        data: {message: message},
        success: function(response) {
            // Append bot response with bot image
            $('#chat-box').append('<div class="message-container bot-message-container"><div class="message">' + response.response + '</div> <img src="/images/bot_gif.gif" alt="Bot" class="bot-image"></div>');
            $('#chat-box').scrollTop($('#chat-box')[0].scrollHeight);
            speakResponse(response.response); // Speak the bot response
        },
        error: function(xhr, status, error) {
            console.error(xhr.responseText);
        }
    });
}

function animateButton() {
    $('#send-button').css('background-color', '#0056b3');
    setTimeout(function() {
        $('#send-button').css('background-color', '#007bff');
    }, 500);
}

// JavaScript for speech recognition
let recognition;

function startListening() {
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.start();

        // Update input box with listening message
        document.getElementById('user-input').value = "Listening...";

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('user-input').value = transcript;
            sendMessage();
        };

        recognition.onerror = function(event) {
            if (event.error === 'no-speech') {
                // Display error message in input box
                document.getElementById('user-input').value = "No speech detected. Please try again.";
            } else if (event.error === 'audio-capture') {
                // Display error message in input box
                document.getElementById('user-input').value = "Audio capture error. Please check your microphone.";
            }
            // You can handle other errors similarly if needed
        };

        recognition.onend = function() {
            console.log('Speech recognition ended');
            // Reset input box after recognition ends
            document.getElementById('user-input').value = "";
        };
    } else {
        console.error('Speech recognition not supported by this browser');
    }
}

// Function to speak the bot's response
function speakResponse(response) {
    var synth = window.speechSynthesis;
    var utterance = new SpeechSynthesisUtterance(response);
    synth.speak(utterance);
}