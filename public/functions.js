
document.getElementById("toPosts").addEventListener("click", function(){
    window.location.href = "posts";
});

var socket;

//initilizes ws on post page startup
function initWS(){
    socket = io.connect('http://' + window.location.host, {transports: ['websocket']});

    socket.on("div_deleted", function(data) {
    var deletionDiv = document.getElementById(data['div_id']);
    deletionDiv.remove();
});

    socket.on("timer_update", function(data){
       var timer = document.getElementById(data[0]);
       timer.textContent = data[1];
    });

}

function postHTML(postJSON){
    const username = postJSON.username;
    const title =postJSON.title;
    const description = postJSON.description;
    const postnumber = postJSON["questionID"];
    const answers = postJSON["answers"];
    const image = postJSON["image"]
    // const likes = postJSON["likes"];

    let thisPostHTML = "";

    thisPostHTML += "<div id= 'div_" +postnumber+"'>";
    thisPostHTML += "<p>Timer(seconds): <span id='timer_" + postnumber+"'>120</span></p><br>"
    // image
    if (image) {
        thisPostHTML += "<img src=public/image/" + image + "><br>";
    }
    thisPostHTML += "<span><b>User: " + username+"<br>Title: " + title+ "</b><br>Description: " +description+"</span><br>";
    // form w/ radio buttons
    thisPostHTML += "<form id=" + postnumber +">Choose your answer:<br>"
    // radio 1
    thisPostHTML += "<input type='radio' id='answer1_' name='answer' value=1>";
    thisPostHTML += "<label for='answer1_'>" + answers[0] + "</label><br>"
    // radio 2
    thisPostHTML += "<input type='radio' id='answer2_' name='answer' value=2>";
    thisPostHTML += "<label for='answer2_'>" + answers[1] + "</label><br>"
    // radio 3
    thisPostHTML += "<input type='radio' id='answer3_' name='answer' value=3>";
    thisPostHTML += "<label for='answer3_'>" + answers[2] + "</label><br>"
    // radio 4
    thisPostHTML += "<input type='radio' id='answer4_' name='answer' value=4>";
    thisPostHTML += "<label for='answer4_'>" + answers[3] + "</label><br>"
    thisPostHTML += "<button type='button' onclick='answerQuestion(" + postnumber +")'> Submit</button>"
    thisPostHTML += "</form><hr>";
    thisPostHTML += "</div>";

    return thisPostHTML;
}

function answerQuestion(questionID){
    const form = document.getElementById(questionID)
    const formData = new FormData(form);
    const jsonData = {"questionID": questionID};
    formData.forEach((value, key) => {
        jsonData[key] = value;
    });
    socket.emit('submit_answer', jsonData);
    //
    disableForm(form);
    // socket.emit('delete_div', {'div_id': 'div_'+questionID})
}

//disables a form after submission. Takes in a form.
function disableForm(form){
    const formElements = form.elements;
    for (let i = 0; i <formElements.length; i++){
        formElements[i].disabled = true;
    }
}




//This just clears all the posts before reload.
function clearPosts(){
    const posts = document.getElementById("all_posts");
    posts.innerHTML = "";
}


function addPosts(postJSON){
    const posts = document.getElementById("all_posts");
    posts.innerHTML += postHTML(postJSON);
    posts.scrollIntoView(false);
    posts.scrollTop = posts.scrollHeight - posts.clientHeight;
}


function updatePosts(){
    const request = new XMLHttpRequest();
    request.onreadystatechange = function(){
      if (this.readyState === 4 && this.status === 200) {
          clearPosts();
          const posts = JSON.parse(this.response);
          for (const post of posts){
              addPosts(post);
          }
      }
    }
    request.open("GET", "/post-history");
    request.send();
}

function username(){
    const request = new XMLHttpRequest();
    request.open("GET", "/user-display");
    request.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            const res = JSON.parse(this.response);
            var usernameDiv = document.getElementById("user");
            usernameDiv.innerHTML = res;
        }
    }
    request.send();
}

function grades(){
    const request = new XMLHttpRequest();
    request.open("GET", "/grades-display");
    request.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            const res = JSON.parse(this.response);
            var gradesDiv = document.getElementById("grades");
            gradesDiv.innerHTML = res;
        }
    }
    request.send();
}

function startup(){
    initWS();
    updatePosts();
}
