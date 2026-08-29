const song = [
    "./song/zzz1years.mp3",
    "./song/zzzbibian.mp3",
    "./song/zzzno_way.mp3",
    "./song/zzzOriginalMe.mp3",
    "./song/zzzReDreamingAngel.mp3",
    "./song/zzzstarlight.mp3",
    "./song/zzzTInygiant.mp3"
];

const songname = [
    "1주년",
    "오시카츠천사비비안짱",
    "싫어!",
    "OriginalMe",
    "ReDreamingAngel",
    "스타라이트 빌리",
    "Tinygiant"
];
const review = document.querySelector('#review p');
    const reviewall = document.querySelector('#review');

    const audio = new Audio();
    let num = 0;
    const button = document.querySelector('#button')
    button.addEventListener('click',function (){


            if (audio.paused == true) {
                num = Math.floor(Math.random()*song.length)
                audio.src =song[num]
                audio.load()
                audio.play()
            reviewall.style.display = 'flex';
            button.innerText= "눌러서 끄기!!(*^_^*)";
            review.innerText = "이노래 어때용???(✿◡‿◡) "+ "/ 제목: " + songname[num]


        }
        else {
            audio.pause()
            reviewall.style.display = 'none';
            button.innerText="오늘의 노랭!!!\\^o^/"
        }
    });


