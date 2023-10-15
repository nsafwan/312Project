
document.getElementById("toPosts").addEventListener("click", function(){
    window.location.href = "posts";
});


//Not completed yet
function postHTML(postJSON){
    const username = postJSON.username;
    const title =postJSON.title;
    const description = postJSON.desc;
    const postnumber = postJSON.postnumber;
    let thisPostHTML = "<br><id =post"

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

//Whatever the user puts into the title and desc box is sent to the server.
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
    titlebox.focus();

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

function startup(){
    document.getElementById("title-box").focus();
    updatePosts();
    setInterval(updatePosts, 2000);
}
