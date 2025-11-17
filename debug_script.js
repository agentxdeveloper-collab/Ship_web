// 디버그용 JavaScript 스크립트
console.log('Script loaded!');

// 팝업 버튼 클릭 이벤트
document.addEventListener('click', function(e) {
  console.log('Click event:', e.target, 'classList:', e.target.classList);
  
  if (e.target.classList.contains('btn-popup')) {
    console.log('Popup button clicked!');
    const city = e.target.getAttribute('data-city');
    const port = e.target.getAttribute('data-port'); 
    const date = e.target.getAttribute('data-date');
    console.log('Popup data:', {city, port, date});
    
    // 팝업 열기
    const popup = document.getElementById('weather-popup');
    if (popup) {
      popup.style.display = 'block';
      console.log('Popup opened!');
    } else {
      console.error('Popup element not found!');
    }
  }
});

// 팝업 닫기
function closeWeatherPopup() {
  const popup = document.getElementById('weather-popup');
  if (popup) {
    popup.style.display = 'none';
    console.log('Popup closed!');
  }
}