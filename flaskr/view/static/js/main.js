
/**
 * Function calls the backend to force update the database.
 */
async function update(){

    buttonElement = document.getElementById("reload");

    buttonElement.innerText = "loading...";

    // Minimal error handling in case backend fails or fetch times out.
    try{

        promise = fetch("http://localhost:80/data/update", {method : "POST"});

        await promise;

    }catch(error){

        console.log(error);

    }

    buttonElement.innerText = "Update Database";
}


/**
 * Function calls the backend and retrives chatterbot response
 */
async function getResponse(event){


    event.preventDefault();

    inputElement = document.getElementById("user-input");
    input = inputElement.value;
    inputElement.value = "";

    chatRegion = document.getElementById("chat-region");

    // Create container
    speechRegion = document.createElement("div");
    speechRegion.classList.add("right-container");
    chatRegion.appendChild(speechRegion);

    // Add speech bubble
    speechBubble = document.createElement("p");
    speechBubble.classList.add("speech-bubble")
    speechBubble.style = "background-color : rgb(25, 38, 75)";
    speechBubble.innerText = input;
    speechRegion.appendChild(speechBubble);

    // User icon
    circularIcon = document.createElement("img");
    circularIcon.src = "/static/images/user.png";
    circularIcon.classList.add("icon-right");
    speechRegion.appendChild(circularIcon);

    // Create container
    speechRegion = document.createElement("div");
    speechRegion.classList.add("left-container");
    chatRegion.appendChild(speechRegion);

    // Bot icon
    circularIcon = document.createElement("img");
    circularIcon.src = "/static/images/bot.png";
    circularIcon.classList.add("icon-left");
    speechRegion.appendChild(circularIcon);

    // Speech bubble
    speechBubble = document.createElement("p");
    speechBubble.classList.add("speech-bubble");
    speechBubble.style = "background-color : rgb(60, 30, 30)";
    speechBubble.innerText = "Loading...";
    speechRegion.appendChild(speechBubble);

    chatRegion.scrollTop += 200;

    response = null

    // Minimal error handling in case backend fails or fetch times out.
    try{

        params = encodeURIComponent(input)

        response = await fetch("http://localhost:80/chat/" + params, { method : "GET"});

    }catch(error){

        console.log(error);
        speechBubble.innerText = "Sorry something went wrong please try again...";

    }
    
    if(response !== null){
        data = await response.json();
        speechBubble.innerText = data["Go Travel Bot"];
    }

    chatRegion.scrollTop += 200;   
}

