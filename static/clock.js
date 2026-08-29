        const date = document.querySelector('#date')
    const clock = document.querySelector('#clock')

    function updatetime () {
        const time = new Date();
        const date1 = time.toLocaleDateString('sv-SE');
        date.innerText = date1
        const clock1 = time.toTimeString().slice(2, 8);
        let hours = time.getHours();


        if (hours > 12) {

            hours = parseInt(hours);
            hours =hours - 12;
            hours = String(hours);
            clock.innerText = hours+clock1 + "PM"

        }
        else {
            clock.innerText = hours+clock1  + "AM"
        }

    }

    setInterval(updatetime,1000);


        const song = [
            "/song/zzz1years.mp3",
            "/song/zzzbibian.mp3",
            "/song/zzzno_way.mp3",
            "/song/zzzOriginalMe.mp3",
            "/song/zzzReDreamingAngel.mp3",
            "/song/zzzstarlight.mp3",
            "/song/zzzTInygiant.mp3"
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


    let num = 0;


    const audio = new Audio();


    const songtext = document.querySelector("#song_text h1");


    function playMusic(index) {

        num = index;

        audio.src = song[num];

        audio.load();

        audio.play();

        songtext.innerText = songname[num];
        animateNeonGlow();

    }


    /* 제목 클릭 → 랜덤 재생 */

    songtext.addEventListener("click", function () {

        num = Math.floor(Math.random() * song.length);

        playMusic(num);

    });


    /* 5초 스킵 */

    const skip = document.querySelector("#skip");


    skip.addEventListener("click", function () {

        audio.currentTime += 5;

    });


    /* 시간 표시 */

    const sec = document.querySelector("#sec h2");


    audio.addEventListener("timeupdate", function () {

        sec.innerText = Math.floor(audio.currentTime) + " sec";

    });


    /* 끝나면 랜덤 다음 곡 */

    audio.addEventListener("ended", function () {

        let nextNum = Math.floor(Math.random() * song.length);

        playMusic(nextNum);

    });


    /* 일시정지 */

    const pause = document.querySelector("#pause h2");


    pause.addEventListener("click", function () {


        if (audio.paused) {

            audio.play();

            pause.innerText = "pause";

        } else {

            audio.pause();

            pause.innerText = "play";

        }


    });

    const Rewind = document.querySelector("#back");


    Rewind.addEventListener("click", function () {

        audio.currentTime -= 5;

    });

