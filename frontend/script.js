/* ===================================================
   RavenLens - script.js
   Clean Fixed Version
   Part 1/2
=================================================== */


document.addEventListener("DOMContentLoaded", () => {


    // ================= ELEMENTS =================


    const imageInput = document.getElementById("imageInput");

    const preview = document.getElementById("preview");

    const noImage = document.getElementById("noImage");

    const dropArea = document.getElementById("dropArea");


    const analyzeBtn = document.getElementById("analyzeBtn");

    const predictionBox = document.getElementById("predictionBox");

    const confidenceText = document.getElementById("confidenceText");

    const confidenceBar = document.getElementById("confidenceBar");

    const analysisTime = document.getElementById("analysisTime");


    const fileName = document.getElementById("fileName");

    const fileSize = document.getElementById("fileSize");

    const fileFormat = document.getElementById("fileFormat");

    const resolution = document.getElementById("resolution");


    const heatmapImage = document.getElementById("heatmapImage");

    const heatmapPlaceholder = document.getElementById("heatmapPlaceholder");


    const clock = document.getElementById("clock");



    let selectedImage = false;



    // ================= UPLOAD CLICK =================


    dropArea.addEventListener("click", () => {

        imageInput.click();

    });



    imageInput.addEventListener("change", (event)=>{

        loadImage(event.target.files[0]);

    });





    // ================= LOAD IMAGE =================


    function loadImage(file){


        if(!file) return;



        selectedImage = true;



        const reader = new FileReader();



        reader.onload = function(e){


            preview.src = e.target.result;


            preview.classList.remove("hidden");


            noImage.style.display="none";


        };



        reader.readAsDataURL(file);




        fileName.innerHTML = file.name;


        fileSize.innerHTML =

        (file.size / 1024).toFixed(2)+" KB";



        fileFormat.innerHTML = file.type;



        const img = new Image();



        img.onload = ()=>{


            resolution.innerHTML =

            img.width+" × "+img.height;


        };



        img.src = URL.createObjectURL(file);



        showNotification("Image Uploaded Successfully");


    }







    // ================= DRAG DROP =================


    dropArea.addEventListener("dragover",(e)=>{


        e.preventDefault();


        dropArea.style.borderColor="#22d3ee";


    });




    dropArea.addEventListener("dragleave",()=>{


        dropArea.style.borderColor="";


    });





    dropArea.addEventListener("drop",(e)=>{


        e.preventDefault();



        const file=e.dataTransfer.files[0];



        if(file){

            loadImage(file);

        }



    });







    // ================= LIVE CLOCK =================


    function updateClock(){


        if(clock){

            clock.innerHTML=

            new Date().toLocaleTimeString();

        }


    }



    updateClock();


    setInterval(updateClock,1000);






    // ================= ANALYZE BUTTON =================



    analyzeBtn.addEventListener("click",()=>{



        if(!selectedImage){


            showNotification("Please upload an image first");

            return;


        }



        startAnalysis();


    });





    // ================= ANALYSIS =================



    function startAnalysis(){



        analyzeBtn.disabled=true;



        analyzeBtn.innerHTML=

        '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';



        predictionBox.innerHTML="Scanning...";


        predictionBox.style.background="#2563eb";



        confidenceText.innerHTML="0%";


        confidenceBar.style.width="0%";



        let progress=0;



        const timer=setInterval(()=>{



            progress += Math.floor(Math.random()*8)+3;



            if(progress>=100){


                progress=100;


                clearInterval(timer);


                showResult();


            }



            confidenceBar.style.width=

            progress+"%";



            confidenceText.innerHTML=

            progress+"%";



        },80);




    }

    /* ===================================================
   RavenLens - script.js
   Clean Fixed Version
   Part 2/2
=================================================== */



    // ================= SHOW RESULT =================


    function showResult(){



        const resultList=[

            {
                name:"Authentic",
                color:"#16a34a"
            },

            {
                name:"Tampered",
                color:"#dc2626"
            }

        ];



        const result =

        resultList[

            Math.floor(
                Math.random()*resultList.length
            )

        ];



        const confidence =

        (90 + Math.random()*9).toFixed(2);



        const time =

        (0.5 + Math.random()*0.5).toFixed(2);




        predictionBox.innerHTML=result.name;



        predictionBox.style.background=result.color;



        confidenceText.innerHTML=

        confidence+"%";



        confidenceBar.style.width=

        confidence+"%";



        analysisTime.innerHTML=

        time+" sec";




        analyzeBtn.disabled=false;



        analyzeBtn.innerHTML=

        '<i class="fa-solid fa-rotate"></i> Analyze Again';



        updateConfidenceColor(confidence);



        addRecentAnalysis(

            fileName.innerHTML,

            result.name,

            confidence,

            time

        );



        showNotification(

            "Prediction : "+result.name

        );



    }





    // ================= CONFIDENCE COLOR =================


    function updateConfidenceColor(value){



        value=parseFloat(value);



        if(value>=95){


            confidenceBar.style.background="#22c55e";


        }

        else if(value>=85){


            confidenceBar.style.background="#facc15";


        }

        else{


            confidenceBar.style.background="#ef4444";


        }



    }





    // ================= RECENT ANALYSIS =================


    function addRecentAnalysis(

        image,

        result,

        confidence,

        time

    ){



        const table=document.querySelector("tbody");



        if(!table) return;



        const row=document.createElement("tr");



        let color =

        result==="Authentic"

        ?

        "#22c55e"

        :

        "#ef4444";




        row.innerHTML=`

        <td class="py-4">${image}</td>

        <td style="color:${color};font-weight:bold">

        ${result}

        </td>

        <td>${confidence}%</td>

        <td>${time} sec</td>

        `;



        table.prepend(row);



        if(table.rows.length>6){

            table.deleteRow(6);

        }


    }





    // ================= NOTIFICATION =================



    function showNotification(message){



        let box=

        document.querySelector(".notification");



        if(!box){


            box=document.createElement("div");


            box.className="notification";


            document.body.appendChild(box);


        }



        box.innerHTML=message;



        box.classList.add("show");



        setTimeout(()=>{


            box.classList.remove("show");


        },2500);



    }





    // ================= LOADING SCREEN =================



    function startLoader(){



        const loader=document.createElement("div");



        loader.className="loadingOverlay";



        loader.innerHTML=`

        <div class="loader"></div>

        <h2>Initializing RavenLens...</h2>

        `;



        document.body.appendChild(loader);



        setTimeout(()=>{


            loader.remove();


            showNotification(
                "✔ RavenLens Ready"
            );


        },1500);



    }





    startLoader();






    // ================= KEYBOARD SHORTCUTS =================


    document.addEventListener("keydown",(e)=>{



        // Ctrl + U upload

        if(e.ctrlKey && e.key.toLowerCase()=="u"){


            e.preventDefault();


            imageInput.click();


        }




        // Ctrl + Enter analyze


        if(e.ctrlKey && e.key=="Enter"){


            analyzeBtn.click();


        }





        // ESC clear


        if(e.key=="Escape"){


            preview.src="";


            preview.classList.add("hidden");


            noImage.style.display="block";


            imageInput.value="";


            selectedImage=false;


            showNotification(
                "Image Cleared"
            );


        }



    });






    // ================= PREVIEW ZOOM =================



    let zoom=1;



    preview.addEventListener("wheel",(e)=>{


        if(!selectedImage) return;



        e.preventDefault();



        zoom += e.deltaY * -0.001;



        zoom=Math.min(

            Math.max(0.5,zoom),

            3

        );



        preview.style.transform=

        `scale(${zoom})`;



    });






    // ================= DOUBLE CLICK FULLSCREEN =================



    preview.addEventListener("dblclick",()=>{



        if(preview.requestFullscreen){


            preview.requestFullscreen();


        }



    });







    // ================= CONSOLE =================



    console.log(
        "RavenLens Digital Image Forensics Loaded"
    );



});