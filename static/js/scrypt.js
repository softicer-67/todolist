function imageZoom(imgID, resultID) {
  var img, lens, result, cx, cy;
  img = document.getElementById(imgID);
  result = document.getElementById(resultID);
  /* Создать объектив: */
  lens = document.createElement("DIV");
  lens.setAttribute("class", "img-zoom-lens");
  /* Вставить линзы: */
  img.parentElement.insertBefore(lens, img);
  /* Вычислите соотношение между результатом DIV и объективом: */
  cx = result.offsetWidth / lens.offsetWidth;
  cy = result.offsetHeight / lens.offsetHeight;
  /* Установите свойства фона для результата DIV */
  result.style.backgroundImage = "url('" + img.src + "')";
  result.style.backgroundSize = (img.width * cx) + "px " + (img.height * cy) + "px";
  /* Выполнение функции при наведении курсора на изображение или объектив: */
  lens.addEventListener("mousemove", moveLens);
  img.addEventListener("mousemove", moveLens);
  /* А также для сенсорных экранов: */
  lens.addEventListener("touchmove", moveLens);
  img.addEventListener("touchmove", moveLens);
  function moveLens(e) {
    var pos, x, y;
    /* Предотвратите любые другие действия, которые могут возникнуть при перемещении по изображению */
    e.preventDefault();
    /* Получить позиции курсора x и y: */
    pos = getCursorPos(e);
    /* Вычислите положение объектива: */
    x = pos.x - (lens.offsetWidth / 2);
    y = pos.y - (lens.offsetHeight / 2);
    /* Не допускайте размещения объектива за пределами изображения: */
    if (x > img.width - lens.offsetWidth) {x = img.width - lens.offsetWidth;}
    if (x < 0) {x = 0;}
    if (y > img.height - lens.offsetHeight) {y = img.height - lens.offsetHeight;}
    if (y < 0) {y = 0;}
    /* Установите положение объектива: */
    lens.style.left = x + "px";
    lens.style.top = y + "px";
    /* Отображение того, что "видит" объектив: */
    result.style.backgroundPosition = "-" + (x * cx) + "px -" + (y * cy) + "px";
  }
  function getCursorPos(e) {
    var a, x = 0, y = 0;
    e = e || window.event;
    /* Получить x и y позиции изображения: */
    a = img.getBoundingClientRect();
    /* Вычислите координаты курсора x и y относительно изображения: */
    x = e.pageX - a.left;
    y = e.pageY - a.top;
    /* Рассмотрим любую прокрутку страницы: */
    x = x - window.pageXOffset;
    y = y - window.pageYOffset;
    return {x : x, y : y};
  }
}