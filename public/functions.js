
document.getElementById("toPosts").addEventListener("click", function(){
    window.location.href = "posts";
});




function initWS(){
    var socket = io.connect('http://' + window.location.host, {transports: ['websocket']});
    socket.on('connect', function(){
    console.log('Connected to server');
});
}



//Not completed yet
function postHTML(postJSON){
    const username = postJSON.username;
    const title =postJSON.title;
    const description = postJSON.description;
    const postnumber = postJSON["questionId"];
    const answers = postJSON["answers"];
    const image = postJSON["image"]
    // const likes = postJSON["likes"];

    let thisPostHTML = "";

    // image
    if (image) {
        thisPostHTML += "<img src=public/image/" + image + "></img><br>"
    }

    thisPostHTML += "<span id='post_" + postnumber +"'><b>User: " + username+"<br>Title: " + title+ "</b><br>Description: " +description+"</span><br>";
    // form w/ radio buttons
    thisPostHTML += "<form>Choose your answer:<br>"
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
    thisPostHTML += "</form><hr>";

    return thisPostHTML;
}

// function likePost(postnumber) {
//     const request = new XMLHttpRequest();
//     request.onreadystatechange = function () {
//         if (this.readyState === 4 && this.status === 200) {
//             console.log(this.response);
//         }
//     }
//     request.open("POST", "/like/" + postnumber);
//     request.send();
// }


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

// Whatever the user puts into the title and desc box is sent to the server.
function sendPost(){
    const titlebox = document.getElementById("title-box");
    const title = titlebox.value;
    titlebox.value = "";
    const descbox = document.getElementById("desc-box");
    const desc = descbox.value
    descbox.value = "";

    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
                console.log(this.response);
        }
    }
    const postJSON= {"title": title, "description": desc};
    request.open("POST", "/submit-post");
    request.send(JSON.stringify(postJSON));

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
    request.onreadystatechange = function(){
      if (this.readyState === 4 && this.status === 200) {
          const res = JSON.parse(this.response)
          var usernameDiv = document.getElementById("user");
          usernameDiv.innerHTML = res;
      }
    }
    request.send()
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
    updatePosts();
    initWS();
}
