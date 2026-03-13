const teamData = [
    {
        name: "이상해신승민씨",
        silhouette: "seungmin/seungmin_silhouette.png",
        image: "seungmin/seungmin.png",
        strengths: [
            { name: "친해지기", desc: "특유의 친화력과 유쾌한 성격으로 팀 분위기를 즐겁게 조성하며, 팀원 전체의 <strong>HP를 100포인트 회복</strong>시킵니다." },
            { name: "적응", desc: "어떤 까다로운 상황이나 환경에서도 유연하게 제 모습을 바꿔 대응하며, 조직 내에서의 <strong>내구력을 100포인트 획득</strong>합니다." },
            { name: "버티기", desc: "한 번 시작한 일은 포기하지 않고 끝까지 물고 늘어지는 집요함으로, 프로젝트의 위기 상황에서도 <strong>HP 1포인트를 남기고 버티며 반드시 완수</strong>합니다." }
        ],
        weaknesses: [
            { name: "성급하기", desc: "의욕이 앞서는 성격 탓에 충분한 준비 없이 일단 부딪히는 경향이 있으며, 예상치 못한 변수 발생 시 <strong>데미지를 4배로 받습니다.</strong>" },
            { name: "결과주의", desc: "과정보다는 결과를 더욱 중시하는 특성이 있어 모두가 노력한 결과가 실패했을 때 <strong>다른 사람들보다 데미지를 4배 받고 '자책' 디버프에 걸립니다.</strong>" }
        ]
    },
    {
        name: "태이리",
        silhouette: "taei/taei_silhouette.png",
        image: "taei/taei.png",
        strengths: [
            { name: "소통하기", desc: "주변 사람들과 지식 및 에너지를 아낌없이 공유하며 팀의 분위기를 끌어올리고, 다음 차례 팀원의 스킬 <strong>데미지를 1.5배 상승</strong>시킵니다." },
            { name: "용의춤", desc: "한 분야에 머무르지 않고 끊임없이 새로운 분야에 도전하며 스스로를 발전시킵니다. 새로운 분야에 도전할 때마다 <strong>공격력과 스피드가 각각 50포인트씩 영구적으로 상승</strong>합니다." }
        ],
        weaknesses: [
            { name: "오버히트", desc: "과도한 열정을 쏟아 목표를 달성하지만, 스스로의 에너지를 급격히 소진하여 <strong>최대 HP의 33% 반동 데미지</strong>를 입습니다." },
            { name: "감정기복", desc: "자신의 내면 상태와 열정이 겉으로 쉽게 드러나는 타입으로, 현재 <strong>HP(컨디션)에 따라 스킬 위력이 변하는 페널티</strong>를 가집니다." }
        ]
    },
    {
        name: "양부기",
        silhouette: "minhyuk/minhyuk_silhouette.png",
        image: "minhyuk/minhyuk.png",
        strengths: [
            { name: "정화", desc: "긍정긍정 에너지로 , 팀원 전체 지침/피곤함/번아웃 <strong>상태이상 100% 치료.</strong>" },
            { name: "리프레쉬", desc: "의견 충돌이나 혼선 같은 팀 내 디버프를 털어내고 하나의 방향으로 정렬하여, 팀 전체의 <strong>협동 공격력을 1.5배 증가</strong>시킵니다." },
            { name: "철벽", desc: "철저한 사전 점검과 준비로 실수 가능성을 낮추며, 마감 직전 결과물의 <strong>방어력을 200 증가</strong>시키고 <strong>적의 공격을 한 번 무효화</strong>합니다." }
        ],
        weaknesses: [
            { name: "과점검", desc: "실수를 막기 위해 무한 검증 모드에 돌입하여 변수를 차단하지만, 자신의 <strong>스피드가 10단계 하락</strong>하며 기다림에 지친 <strong>팀원들의 사기가 소폭 감소</strong>합니다." }
        ]
    }
];

let currentIndex = 0;
let isRevealed = false;
let isMusicPlaying = false;

const silhouetteImg = document.getElementById('character-silhouette');
const colorImg = document.getElementById('character-color');
const infoPanel = document.getElementById('info-panel');
const revealBtn = document.getElementById('reveal-btn');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const bgMusic = document.getElementById('bg-music');

// ★ 오디오 자동 재생 및 예외 처리 로직 ★
bgMusic.volume = 0.3; // 볼륨 30%

// 1. 페이지가 로드되면 자동 재생 시도
let playPromise = bgMusic.play();

if (playPromise !== undefined) {
    playPromise.then(_ => {
        // 브라우저가 자동 재생을 허용했을 경우
        isMusicPlaying = true;
    }).catch(error => {
        // 브라우저가 자동 재생을 차단했을 경우 (가장 흔함)
        console.log("자동 재생이 차단되었습니다. 화면 클릭 시 재생됩니다.");
        
        // 2. 우회 방법: 화면 아무 곳이나 한 번 클릭하면 바로 음악 재생
        document.body.addEventListener('click', function playOnFirstClick() {
            if (!isMusicPlaying) {
                bgMusic.play();
                isMusicPlaying = true;
            }
            // 한 번 재생되면 이 클릭 이벤트는 지워줍니다.
            document.body.removeEventListener('click', playOnFirstClick);
        }, { once: true });
    });
}

function updateUI() {
    const member = teamData[currentIndex];
    
    silhouetteImg.src = member.silhouette;
    colorImg.src = member.image;

    document.getElementById('member-name').textContent = member.name;
    
    const strengthsList = document.getElementById('strengths-list');
    strengthsList.innerHTML = member.strengths.map(s => 
        `<li><span class="skill-name">✨ ${s.name}</span><span class="skill-desc">${s.desc}</span></li>`
    ).join('');

    const weaknessesList = document.getElementById('weaknesses-list');
    weaknessesList.innerHTML = member.weaknesses.map(w => 
        `<li><span class="skill-name">💥 ${w.name}</span><span class="skill-desc">${w.desc}</span></li>`
    ).join('');

    isRevealed = false;
    silhouetteImg.classList.add('active');
    silhouetteImg.classList.remove('hidden');
    colorImg.classList.add('hidden');
    colorImg.classList.remove('active');
    infoPanel.classList.add('hidden');
    revealBtn.textContent = "정체 확인하기!";
}

revealBtn.addEventListener('click', () => {
    isRevealed = !isRevealed;

    if (isRevealed) {
        silhouetteImg.classList.remove('active');
        silhouetteImg.classList.add('hidden');
        colorImg.classList.remove('hidden');
        colorImg.classList.add('active');
        infoPanel.classList.remove('hidden');
        revealBtn.textContent = "실루엣으로 돌아가기";
    } else {
        silhouetteImg.classList.add('active');
        silhouetteImg.classList.remove('hidden');
        colorImg.classList.add('hidden');
        colorImg.classList.remove('active');
        infoPanel.classList.add('hidden');
        revealBtn.textContent = "정체 확인하기!";
    }
});

prevBtn.addEventListener('click', () => {
    currentIndex = (currentIndex === 0) ? teamData.length - 1 : currentIndex - 1;
    updateUI();
});

nextBtn.addEventListener('click', () => {
    currentIndex = (currentIndex === teamData.length - 1) ? 0 : currentIndex + 1;
    updateUI();
});

updateUI();