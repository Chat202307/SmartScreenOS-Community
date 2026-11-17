(function () {
  var homeStatusRevision = null;
  var homeStatusAvailable = null;
  var homeStatusHasData = false;

  var latestDashboardZones = [];
  var latestDashboardDevices = [];
  var latestDashboardDeviceStates = [];
  var latestDashboardLocations = [];
  var activeAreaLocationId = null;

  var dashboardStateEventsConnected = false;
  var semanticDashboardRefreshTimer = null;

  var SEMANTIC_FALLBACK_INTERVAL_MS = 5000;
  var SEMANTIC_CONNECTED_INTERVAL_MS = 30000;
  var weekdays = {
    "Monday": "星期一",
    "Tuesday": "星期二",
    "Wednesday": "星期三",
    "Thursday": "星期四",
    "Friday": "星期五",
    "Saturday": "星期六",
    "Sunday": "星期日"
  };

  function escapeHtml(value) {
    return String(
      value == null ? "" : value
    )
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }


  function formatClockTime(value) {
    if (!value) {
      return "--:--";
    }

    var parts = String(value).split(":");

    if (parts.length < 2) {
      return value;
    }

    return parts.slice(0, 2).join(":");
  }


  function formatDate(date, weekday) {
    if (!date) {
      return "----";
    }

    var parts = date.split("-");
    var text = date;

    if (parts.length === 3) {
      text =
        parseInt(parts[1], 10) + "月" +
        parseInt(parts[2], 10) + "日";
    }

    if (weekdays[weekday]) {
      text += " · " + weekdays[weekday];
    }

    return text;
  }

  function weatherIconClass(value) {
    if (value === "sunny") {
      return "weather-icon-sunny";
    }

    return "weather-icon-cloudy";
  }

  function formatWeatherCondition(value) {
    var labels = {
      "sunny": "晴",
      "clear-night": "晴夜",
      "partlycloudy": "多云",
      "cloudy": "阴",
      "rainy": "雨",
      "pouring": "大雨",
      "lightning": "雷电",
      "lightning-rainy": "雷雨",
      "snowy": "雪",
      "snowy-rainy": "雨夹雪",
      "fog": "雾",
      "hail": "冰雹",
      "windy": "大风",
      "windy-variant": "多风",
      "exceptional": "异常天气"
    };

    if (
      value &&
      Object.prototype.hasOwnProperty.call(
        labels,
        value
      )
    ) {
      return labels[value];
    }

    return value || "--";
  }

  function formatObservedAt(value) {
    if (!value) {
      return "";
    }

    var date = new Date(value);

    if (isNaN(date.getTime())) {
      return "";
    }

    var hours = date.getHours();
    var minutes = date.getMinutes();

    return (
      (hours < 10 ? "0" : "") +
      hours +
      ":" +
      (minutes < 10 ? "0" : "") +
      minutes
    );
  }

  function setUpdateStatus(
    state,
    detail
  ) {
    var node = document.getElementById(
      "update-status"
    );

    if (!node) {
      return;
    }

    var normalizedState =
      state || "pending";

    node.className =
      "update-status update-status-" +
      normalizedState;

    node.innerHTML = "";

    if (detail) {
      node.setAttribute(
        "title",
        detail
      );
    } else {
      node.removeAttribute(
        "title"
      );
    }
  }


  function showConnectionError() {
    setUpdateStatus(
      "error",
      "数据连接失败"
    );
  }

  var photoList = [];
  var photoIndex = 0;

  function showCurrentPhoto() {
    var image = document.getElementById("photo-image");
    var empty = document.getElementById("photo-empty");

    if (photoList.length === 0) {
      image.style.display = "none";
      empty.style.display = "block";
      empty.innerHTML = "暂无照片";
      return;
    }

    image.src = photoList[photoIndex].url;
    image.style.display = "block";
    empty.style.display = "none";
  }

  function showNextPhoto() {
    if (photoList.length <= 1) {
      return;
    }

    photoIndex =
      (photoIndex + 1) % photoList.length;

    showCurrentPhoto();
  }

  function updatePhotoCard() {
    var request = new XMLHttpRequest();

    request.onreadystatechange = function () {
      if (request.readyState !== 4) {
        return;
      }

      var image = document.getElementById("photo-image");
      var empty = document.getElementById("photo-empty");

      if (request.status !== 200) {
        image.style.display = "none";
        empty.style.display = "block";
        empty.innerHTML = "暂无照片";
        return;
      }

      var payload;

      try {
        payload = JSON.parse(request.responseText);
      } catch (error) {
        image.style.display = "none";
        empty.style.display = "block";
        empty.innerHTML = "暂无照片";
        return;
      }

      var photos = payload.photos || [];

      photoList = photos;

      if (photoIndex >= photoList.length) {
        photoIndex = 0;
      }

      showCurrentPhoto();
    };

    request.open("GET", "/api/photos", true);
    request.send();
  }

  var todayCalendarDate = null;
  var todayCalendarEvents = [];
  var todayCalendarUpdatedAt = 0;
  var todayCalendarRefreshMs = 5 * 60 * 1000;
  var todayCalendarState = "syncing";
  var todayCalendarHasSnapshot = false;
  var todayCalendarNextAttemptAt = 0;
  var todayCalendarRequest = null;
  var todayCalendarViewDate = null;
  var todayCalendarWeekday = null;
  var todayCalendarServerOffsetMs = 0;

  function updateCalendarClock(date, time) {
    if (date && typeof time === "string" && /^\d{2}:\d{2}(:\d{2})?$/.test(time)) {
      var value = new Date(date + "T" + time + (time.length === 5 ? ":00" : "") + "+08:00").getTime();
      if (!isNaN(value)) {
        todayCalendarServerOffsetMs = value - Date.now();
      }
    }
  }

  function refreshTodayCalendar() {
    // The existing calendar view and server prewarm both use Shanghai days.
    var date = new Date(Date.now() + todayCalendarServerOffsetMs + 8 * 60 * 60 * 1000).toISOString().slice(0, 10);
    updateTodayCalendar(date, null);
  }

  function calendarTwoDigits(value) {
    return (value < 10 ? "0" : "") + String(value);
  }

  function calendarStatusText() {
    if (todayCalendarState === "fresh") {
      return "";
    }
    if (todayCalendarState === "syncing") {
      return todayCalendarHasSnapshot ? "旧日程·同步中 ›" : "日历同步中…";
    }
    if (todayCalendarState === "stale") {
      return "旧日程·待更新 ›";
    }
    return todayCalendarHasSnapshot ? "旧日程·更新失败 ›" : "日历暂不可用";
  }

  function calendarStatusTitle() {
    if (!todayCalendarHasSnapshot) {
      return calendarStatusText();
    }
    var value = new Date(todayCalendarUpdatedAt);
    return "上次同步 " + calendarTwoDigits(value.getHours()) + ":" +
      calendarTwoDigits(value.getMinutes());
  }

  function calendarVisibleEvents(date) {
    if (!date || todayCalendarDate === date) {
      return todayCalendarEvents;
    }
    // Preserve a previous day's snapshot during an outage, but exclude events
    // whose exclusive end is before today's range (including all-day midnight).
    var start = new Date(date + "T00:00:00+08:00").getTime();
    var end = start + 10 * 24 * 60 * 60 * 1000;
    var result = [];
    for (var index = 0; index < todayCalendarEvents.length; index += 1) {
      var event = todayCalendarEvents[index];
      var begins = new Date(event.start).getTime();
      var ends = new Date(event.end).getTime();
      if (begins < end && (ends > start || (begins === ends && begins >= start))) {
        result.push(event);
      }
    }
    return result;
  }

  function renderCalendarState() {
    renderTodaySummary(todayCalendarViewDate, todayCalendarWeekday);
    if (calendarOverlayIsOpen()) {
      renderCalendarOverlay();
    }
  }


  function renderTodaySummary(
    date,
    weekday
  ) {
    var node = document.getElementById(
      "today-summary"
    );

    if (!node) {
      return;
    }

    /*
     * The dashboard header already shows the current date.
     * Use the Today card entirely for upcoming calendar
     * information instead of repeating the date here.
     */
    var html = "";
    var events = [];

    if (date) {
      events = calendarVisibleEvents(date);
    }

    var visibleCount = Math.min(
      events.length,
      3
    );

    for (
      var index = 0;
      index < visibleCount;
      index += 1
    ) {
      var event = events[index];
      var title = String(
        event.title || ""
      ).trim();

      if (!title) {
        continue;
      }

      var prefix = "今天";

      if (event.start) {
        var eventStart = new Date(
          event.start
        );

        if (!isNaN(eventStart.getTime())) {
          var todayStart = new Date(
            date + "T00:00:00+08:00"
          );

          /*
           * For presentation only, treat a multi-day
           * event that started before today but is still
           * active today as a Today event.
           */
          var displayStart = eventStart;

          if (event.end) {
            var eventEnd = new Date(event.end);

            if (
              !isNaN(todayStart.getTime()) &&
              !isNaN(eventEnd.getTime()) &&
              eventStart.getTime() <
                todayStart.getTime() &&
              eventEnd.getTime() >
                todayStart.getTime()
            ) {
              displayStart = todayStart;
            }
          }

          var eventDay = new Date(
            displayStart.getFullYear(),
            displayStart.getMonth(),
            displayStart.getDate()
          );

          var todayDay = new Date(
            todayStart.getFullYear(),
            todayStart.getMonth(),
            todayStart.getDate()
          );

          var dayOffset = Math.round(
            (
              eventDay.getTime() -
              todayDay.getTime()
            ) /
            (24 * 60 * 60 * 1000)
          );

          if (dayOffset === 1) {
            prefix = "明天";
          } else if (dayOffset > 1) {
            prefix =
              String(
                eventStart.getMonth() + 1
              ) +
              "月" +
              String(
                eventStart.getDate()
              ) +
              "日";
          }

          if (!event.all_day) {
            prefix +=
              " " +
              calendarTwoDigits(eventStart.getHours()) +
              ":" +
              calendarTwoDigits(eventStart.getMinutes());
          }
        }
      }

      if (html) {
        html += "<br>";
      }

      html +=
        escapeHtml(prefix) +
        "  " +
        escapeHtml(title);
    }

    var remainingCount =
      events.length - visibleCount;

    if (html) {
      html += "<br>";
    }

    var statusText = calendarStatusText();
    if (statusText) {
      html += '<span class="today-calendar-more" title="' +
        escapeHtml(calendarStatusTitle()) + '">' +
        escapeHtml(statusText) + "</span>";
    } else if (remainingCount > 0) {
      html +=
        '<span class="today-calendar-more">' +
        "10天内还有 " +
        String(remainingCount) +
        " 项 ›" +
        "</span>";
    } else if (events.length > 0) {
      html +=
        '<span class="today-calendar-more">' +
        "查看未来10天 ›" +
        "</span>";
    } else {
      html +=
        '<span class="today-calendar-more">' +
        "未来10天暂无事项" +
        "</span>";
    }

    node.innerHTML = html;
  }

  function updateTodayCalendar(date, weekday) {
    if (!date) {
      return;
    }
    if (todayCalendarViewDate !== date) {
      todayCalendarNextAttemptAt = 0;
      todayCalendarState = "syncing";
    }
    todayCalendarViewDate = date;
    todayCalendarWeekday = weekday;
    if (todayCalendarState === "fresh" && Date.now() >= todayCalendarNextAttemptAt) {
      todayCalendarState = "syncing";
    }
    renderCalendarState();
    if (todayCalendarRequest || Date.now() < todayCalendarNextAttemptAt) {
      return;
    }
    var start = new Date(date + "T00:00:00+08:00");
    if (isNaN(start.getTime())) {
      return;
    }
    var end = new Date(start.getTime() + 10 * 24 * 60 * 60 * 1000);
    var request = new XMLHttpRequest();
    var settled = false;
    todayCalendarRequest = request;

    function finish(state, payload) {
      if (settled) {
        return;
      }
      settled = true;
      todayCalendarRequest = null;
      var retry = 15;
      if (request.getResponseHeader) {
        var hint = Number(request.getResponseHeader("Retry-After"));
        if (isFinite(hint) && hint > 0) {
          retry = Math.max(5, Math.min(30, hint));
        }
      }
      var age = 0;
      if (payload && (state === "fresh" || state === "stale")) {
        var details = payload.calendar_status || {};
        if (typeof details.age_seconds === "number" &&
            isFinite(details.age_seconds) && details.age_seconds >= 0) {
          age = details.age_seconds * 1000;
        }
        todayCalendarDate = date;
        todayCalendarEvents = payload.events;
        todayCalendarHasSnapshot = true;
        todayCalendarUpdatedAt = Date.now() - age;
        if (state === "fresh" && age >= todayCalendarRefreshMs) {
          state = "stale";
        }
      }
      todayCalendarState = state;
      todayCalendarNextAttemptAt = Date.now() + (state === "fresh" ?
        Math.max(0, todayCalendarRefreshMs - age) : retry * 1000);
      if (date !== todayCalendarViewDate) {
        todayCalendarState = "syncing";
        todayCalendarNextAttemptAt = 0;
      }
      renderCalendarState();
    }

    request.onreadystatechange = function () {
      if (request.readyState !== 4 || settled) {
        return;
      }
      var payload;
      try {
        payload = JSON.parse(request.responseText);
      } catch (error) {
        finish("unavailable");
        return;
      }
      if (request.status !== 200) {
        finish(request.status === 503 && payload && payload.calendar_status &&
          payload.calendar_status.state === "syncing" ? "syncing" : "unavailable");
        return;
      }
      if (!payload || !Array.isArray(payload.events)) {
        finish("unavailable");
        return;
      }
      for (var index = 0; index < payload.events.length; index += 1) {
        if (!payload.events[index] || typeof payload.events[index] !== "object") {
          finish("unavailable");
          return;
        }
      }
      var status = payload.calendar_status || {};
      var stale = status.stale === true || status.state === "stale" ||
        (request.getResponseHeader && request.getResponseHeader("X-Calendar-Stale") === "true");
      if (status.state && status.state !== "fresh" && status.state !== "stale") {
        finish("unavailable");
        return;
      }
      // EventKit's legacy 200 + events response has no calendar_status.
      finish(stale ? "stale" : "fresh", payload);
    };
    request.onerror = request.ontimeout = request.onabort = function () {
      finish("unavailable");
    };
    try {
      request.open("GET", "/api/calendar?start=" + encodeURIComponent(start.toISOString()) +
        "&end=" + encodeURIComponent(end.toISOString()), true);
      request.timeout = 10000;
      request.send();
    } catch (error) {
      finish("unavailable");
    }
  }

  var todoRevision = null;
  var todoItems = [];
  var todoBusy = false;
  var todoShowCompleted = false;
  var todoEditId = null;
  var todoRequestNumber = 0;

  function todoFeedback(message) {
    document.getElementById("todo-feedback").textContent = message;
  }

  function renderTodoSummary() {
    var summary = document.getElementById("todo-summary");
    var pending = [];
    var index;

    for (index = 0; index < todoItems.length; index += 1) {
      if (!todoItems[index].completed) {
        pending.push(todoItems[index]);
      }
    }

    if (!pending.length) {
      summary.textContent = "暂无待办";
      return;
    }

    var html = "";
    var visibleCount = Math.min(pending.length, 2);

    for (index = 0; index < visibleCount; index += 1) {
      html +=
        '<div class="todo-summary-item">' +
        escapeHtml(pending[index].title) +
        "</div>";
    }

    if (pending.length > visibleCount) {
      html +=
        '<div class="todo-summary-more">还有 ' +
        (pending.length - visibleCount) +
        " 项</div>";
    }

    summary.innerHTML = html;
  }

  function renderTodos() {
    document.getElementById("todo-add-button").disabled = !!todoEditId || todoBusy;
    var list = document.getElementById("todo-list");
    var html = "";
    var completedCount = 0;
    var index;
    for (index = 0; index < todoItems.length; index += 1) {
      var todo = todoItems[index];
      if (todo.completed) { completedCount += 1; }
      if (todo.completed && !todoShowCompleted) { continue; }
      var id = escapeHtml(todo.id);
      html += '<div class="todo-item' + (todo.completed ? ' todo-completed' : '') + '">';
      if (todoEditId === todo.id) {
        html += '<input class="todo-edit-input" aria-label="修改待办" maxlength="200" value="' + escapeHtml(todo.title) + '">' +
          '<button type="button" data-todo-action="save" data-todo-id="' + id + '">保存</button>' +
          '<button type="button" data-todo-action="cancel">取消</button>';
      } else {
        html += '<button type="button" class="todo-toggle" aria-label="' + (todo.completed ? '恢复：' : '完成：') + escapeHtml(todo.title) +
          '" data-todo-action="toggle" data-todo-id="' + id + '">' + (todo.completed ? '✓' : '○') + '</button>' +
          '<span class="todo-title">' + escapeHtml(todo.title) + '</span>' +
          '<button type="button" data-todo-action="edit" data-todo-id="' + id + '">编辑</button>' +
          '<button type="button" data-todo-action="delete" data-todo-id="' + id + '">删除</button>';
      }
      html += '</div>';
    }
    list.innerHTML = html || (todoItems.length ? '暂无未完成事项' : '暂无待办');
    var toggle = document.getElementById("todo-show-completed");
    toggle.textContent = (todoShowCompleted ? '收起已完成' : '查看已完成') + '（' + completedCount + '）';
    toggle.setAttribute('aria-pressed', todoShowCompleted ? 'true' : 'false');
    renderTodoSummary();
  }

  function updateTodoCard() {
    if (todoBusy || todoEditId) { return; }
    var number = ++todoRequestNumber;
    var request = new XMLHttpRequest();
    request.onreadystatechange = function () {
      if (request.readyState !== 4 || number !== todoRequestNumber || todoBusy || todoEditId) { return; }
      if (request.status !== 200) {
        todoRevision = null;
        todoFeedback('待办读取失败，稍后自动重试');
        if (!todoItems.length) {
          document.getElementById('todo-summary').textContent = '待办暂不可用';
          document.getElementById('todo-list').textContent = '待办暂不可用';
        }
        return;
      }
      try {
        var payload = JSON.parse(request.responseText);
        if (!Array.isArray(payload.todos) || typeof payload.revision !== 'string') { throw new Error('invalid todos'); }
        todoItems = payload.todos;
        todoRevision = payload.revision;
        renderTodos();
        todoFeedback('');
      } catch (error) {
        todoRevision = null;
        todoFeedback('待办数据异常，请检查保存文件');
      }
    };
    request.open("GET", "/api/todos", true);
    request.timeout = 10000;
    request.send();
  }

  function saveTodo(change, onSuccess) {
    if (todoBusy) { return; }
    if (!todoRevision) { todoFeedback('请等待待办加载成功后再操作'); return; }
    change.revision = todoRevision;
    todoBusy = true;
    todoRequestNumber += 1;
    document.getElementById('todo-add-button').disabled = true;
    todoFeedback('正在保存…');
    var request = new XMLHttpRequest();
    request.onreadystatechange = function () {
      if (request.readyState !== 4) { return; }
      todoBusy = false;
      document.getElementById('todo-add-button').disabled = !!todoEditId;
      if (request.status === 200) {
        try {
          var payload = JSON.parse(request.responseText);
          todoItems = payload.todos;
          todoRevision = payload.revision;
          todoEditId = null;
          renderTodos();
          todoFeedback('已保存');
          if (onSuccess) { onSuccess(); }
        } catch (error) { todoFeedback('保存结果未知，请刷新后核对'); }
      } else if (request.status === 409) {
        // Preserve an active edit. Other operations can safely
        // reload the authoritative list and revision immediately.
        todoRevision = null;
        todoFeedback('其他屏幕已修改待办。请保留输入，取消编辑或刷新后重试');
        if (!todoEditId) {
          updateTodoCard();
        }
      } else {
        todoFeedback(request.status === 400 ? '请填写 1–200 字的待办，列表最多 1000 项' : '保存未确认，请刷新核对后重试；输入已保留');
        if (request.status === 0) { todoRevision = null; }
      }
    };
    request.open('POST', '/api/todos', true);
    request.setRequestHeader('Content-Type', 'application/json');
    request.timeout = 10000;
    request.send(JSON.stringify(change));
  }

  function calendarOverlayIsOpen() {
    var overlay = document.getElementById(
      "calendar-overlay"
    );

    if (!overlay) {
      return false;
    }

    return (
      (" " + overlay.className + " ")
        .indexOf(" calendar-overlay-open ") !== -1
    );
  }

  function calendarEventDayLabel(event) {
    if (!event || !event.start) {
      return "";
    }

    var value = new Date(event.start);

    if (isNaN(value.getTime())) {
      return "";
    }

    /*
     * A multi-day event may have started before today
     * while still being active today. Calendar API
     * correctly returns overlapping events, so present
     * such an event under Today instead of its historical
     * start date.
     */
    if (
      todayCalendarViewDate &&
      event.end
    ) {
      var todayStart = new Date(
        todayCalendarViewDate +
        "T00:00:00+08:00"
      );
      var eventEnd = new Date(event.end);

      if (
        !isNaN(todayStart.getTime()) &&
        !isNaN(eventEnd.getTime()) &&
        value.getTime() <
          todayStart.getTime() &&
        eventEnd.getTime() >
          todayStart.getTime()
      ) {
        value = todayStart;
      }
    }

    var month = value.getMonth() + 1;
    var day = value.getDate();

    var weekdays = [
      "周日",
      "周一",
      "周二",
      "周三",
      "周四",
      "周五",
      "周六"
    ];

    var label =
      String(month) +
      "月" +
      String(day) +
      "日 " +
      weekdays[value.getDay()];

    if (
      todayCalendarViewDate &&
      value.getFullYear() ===
        new Date(
          todayCalendarViewDate +
          "T00:00:00+08:00"
        ).getFullYear() &&
      value.getMonth() ===
        new Date(
          todayCalendarViewDate +
          "T00:00:00+08:00"
        ).getMonth() &&
      value.getDate() ===
        new Date(
          todayCalendarViewDate +
          "T00:00:00+08:00"
        ).getDate()
    ) {
      return "今天 " + weekdays[value.getDay()];
    }

    return label;
  }

  function calendarEventTimeLabel(event) {
    if (!event) {
      return "";
    }

    if (event.all_day) {
      return "全天";
    }

    if (!event.start) {
      return "";
    }

    var value = new Date(event.start);

    if (isNaN(value.getTime())) {
      return "";
    }

    return (
      calendarTwoDigits(value.getHours()) +
      ":" +
      calendarTwoDigits(value.getMinutes())
    );
  }

  function renderCalendarOverlay() {
    var list = document.getElementById(
      "calendar-overlay-list"
    );

    if (!list) {
      return;
    }

    var eyebrow = document.querySelector(".calendar-overlay-eyebrow");
    if (eyebrow) {
      eyebrow.innerHTML = escapeHtml(calendarStatusText() || "家庭日历");
      eyebrow.title = calendarStatusTitle();
    }
    var events = calendarVisibleEvents(todayCalendarViewDate);
    if (!events.length) {
      list.innerHTML =
        '<div class="calendar-overlay-empty">' +
        escapeHtml(calendarStatusText() || "未来 10 天暂无日历事项") +
        "</div>";
      return;
    }

    var html = "";
    var previousDay = "";

    for (
      var index = 0;
      index < events.length;
      index += 1
    ) {
      var event = events[index];
      var title = String(
        event.title || ""
      ).trim();

      if (!title) {
        continue;
      }

      var dayLabel = calendarEventDayLabel(event);

      if (dayLabel !== previousDay) {
        html +=
          '<div class="calendar-overlay-day">' +
          escapeHtml(dayLabel) +
          "</div>";

        previousDay = dayLabel;
      }

      html +=
        '<div class="calendar-overlay-event">' +
          '<div class="calendar-overlay-time">' +
            escapeHtml(
              calendarEventTimeLabel(event)
            ) +
          "</div>" +
          '<div class="calendar-overlay-event-title">' +
            escapeHtml(title) +
          "</div>" +
        "</div>";
    }

    if (!html) {
      html =
        '<div class="calendar-overlay-empty">' +
        escapeHtml(calendarStatusText() || "未来 10 天暂无日历事项") +
        "</div>";
    }

    list.innerHTML = html;
  }

  function openCalendarOverlay() {
    var overlay = document.getElementById(
      "calendar-overlay"
    );
    var dashboard = document.querySelector(
      ".dashboard"
    );

    if (!overlay) {
      return;
    }

    overlay.className =
      "calendar-overlay calendar-overlay-open";
    overlay.setAttribute(
      "aria-hidden",
      "false"
    );

    if (dashboard) {
      dashboard.className =
        "dashboard calendar-background-blurred";
    }

    renderCalendarOverlay();
  }

  function closeCalendarOverlay() {
    var overlay = document.getElementById(
      "calendar-overlay"
    );
    var dashboard = document.querySelector(
      ".dashboard"
    );

    if (!overlay || !calendarOverlayIsOpen()) {
      return;
    }

    overlay.className = "calendar-overlay";
    overlay.setAttribute(
      "aria-hidden",
      "true"
    );

    if (dashboard) {
      dashboard.className = "dashboard";
    }

    var card = document.getElementById(
      "today-card"
    );

    if (card) {
      card.blur();
    }
  }

  function bindCalendarOverlay() {
    var card = document.getElementById(
      "today-card"
    );

    if (!card) {
      return;
    }

    var lastCalendarCardTouchAt = 0;

    /*
     * Keep the same legacy-iPad interaction model
     * already verified by the Todo card.
     */
    card.ontouchstart = function () {
      lastCalendarCardTouchAt = Date.now();
      openCalendarOverlay();
    };

    card.onclick = function () {
      if (
        lastCalendarCardTouchAt &&
        Date.now() - lastCalendarCardTouchAt < 700
      ) {
        return;
      }

      openCalendarOverlay();
    };

    card.onkeydown = function (event) {
      if (
        event.key === "Enter" ||
        event.key === " "
      ) {
        event.preventDefault();
        openCalendarOverlay();
      }
    };

    var closeButtons =
      document.querySelectorAll(
        "[data-calendar-close]"
      );

    for (
      var index = 0;
      index < closeButtons.length;
      index += 1
    ) {
      closeButtons[index].onclick =
        closeCalendarOverlay;
    }
  }

  function todoOverlayIsOpen() {
    var overlay = document.getElementById("todo-overlay");
    return (
      (" " + overlay.className + " ")
        .indexOf(" todo-overlay-open ") !== -1
    );
  }

  function openTodoOverlay() {
    var overlay = document.getElementById("todo-overlay");
    var dashboard = document.querySelector(".dashboard");

    overlay.className =
      "todo-overlay todo-overlay-open";
    overlay.setAttribute("aria-hidden", "false");

    if (dashboard) {
      dashboard.className =
        "dashboard todo-background-blurred";
    }

    renderTodos();
  }

  function closeTodoOverlay() {
    var overlay = document.getElementById("todo-overlay");
    var dashboard = document.querySelector(".dashboard");

    if (!todoOverlayIsOpen()) {
      return;
    }

    todoEditId = null;
    overlay.className = "todo-overlay";
    overlay.setAttribute("aria-hidden", "true");

    if (dashboard) {
      dashboard.className = "dashboard";
    }

    renderTodos();

    var card = document.getElementById("todo-card");
    if (card) {
      card.blur();
    }
  }

  function bindTodos() {
    var card = document.getElementById('todo-card');

    var lastTodoCardTouchAt = 0;

    /*
     * Legacy iPad Safari:
     *
     * The dedicated SmartScreen iPad has been verified to
     * deliver touchstart reliably, while touchend is not
     * reliable for this non-native card.
     *
     * Open on touchstart and suppress only the synthetic
     * click that Safari may emit immediately afterwards.
     */
    card.ontouchstart = function () {
      lastTodoCardTouchAt = Date.now();
      openTodoOverlay();
    };

    card.onclick = function () {
      if (
        lastTodoCardTouchAt &&
        Date.now() - lastTodoCardTouchAt < 700
      ) {
        return;
      }

      openTodoOverlay();
    };

    card.onkeydown = function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openTodoOverlay();
      }
    };

    var closeButtons = document.querySelectorAll('[data-todo-close]');
    for (var closeIndex = 0; closeIndex < closeButtons.length; closeIndex += 1) {
      closeButtons[closeIndex].onclick = closeTodoOverlay;
    }

    document.getElementById('todo-add-form').onsubmit = function (event) {
      event.preventDefault();
      if (todoEditId) { todoFeedback('请先保存或取消正在编辑的待办'); return; }
      var input = document.getElementById('todo-new-title');
      if (!input.value.replace(/\s/g, '')) { todoFeedback('请填写待办内容'); return; }
      saveTodo({op: 'create', title: input.value}, function () { input.value = ''; });
    };
    document.getElementById('todo-show-completed').onclick = function () {
      if (todoBusy || todoEditId) { return; }
      todoShowCompleted = !todoShowCompleted;
      renderTodos();
    };
    document.getElementById('todo-list').onclick = function (event) {
      var target = event.target;
      var action = target.getAttribute('data-todo-action');
      if (!action || todoBusy) { return; }
      var id = target.getAttribute('data-todo-id');
      var item = null;
      for (var i = 0; i < todoItems.length; i += 1) { if (todoItems[i].id === id) { item = todoItems[i]; break; } }
      if (action === 'cancel') { todoEditId = null; renderTodos(); updateTodoCard(); }
      else if (action === 'edit') { if (todoEditId) { todoFeedback('请先保存或取消当前编辑'); return; } todoEditId = id; renderTodos(); document.querySelector('.todo-edit-input').focus(); }
      else if (action === 'save') { saveTodo({op: 'update', id: id, title: target.parentNode.querySelector('input').value}); }
      else if (action === 'toggle' && item && !todoEditId) { saveTodo({op: 'update', id: id, completed: !item.completed}); }
      else if (action === 'delete' && item && !todoEditId && window.confirm('删除这条待办？\n' + item.title)) { saveTodo({op: 'delete', id: id}); }
    };
  }

  document.addEventListener('keydown', function (event) {
    if (
      event.key === 'Escape' &&
      calendarOverlayIsOpen()
    ) {
      closeCalendarOverlay();
      return;
    }

    if (event.key === 'Escape' && todoOverlayIsOpen()) {
      closeTodoOverlay();
    }
  });


  function homeStatusClass(state) {
    if (
      state === "开启" ||
      state === "有人" ||
      state === "已打开" ||
      state === "制冷"
    ) {
      return "state-active";
    }

    if (
      state === "关闭" ||
      state === "无人" ||
      state === "已关闭"
    ) {
      return "state-inactive";
    }

    if (state === "离线") {
      return "state-warning";
    }

    if (state === "未知") {
      return "state-unknown";
    }

    return "";
  }

  var homeActionBusy = false;
  var homeCoverLastAction = {};
  var homeActionErrorTimeout = null;

  function showHomeActionError(homeList) {
    if (!homeList) {
      return;
    }

    if (
      homeList.className.indexOf(
        "home-action-error"
      ) === -1
    ) {
      homeList.className += " home-action-error";
    }

    if (homeActionErrorTimeout) {
      clearTimeout(
        homeActionErrorTimeout
      );
    }

    homeActionErrorTimeout = setTimeout(
      function () {
        homeList.className = homeList.className.replace(
          / ?home-action-error/g,
          ""
        );

        homeActionErrorTimeout = null;
      },
      1500
    );
  }

  function performHomeAction(
    entityId,
    action
  ) {
    if (homeActionBusy) {
      return;
    }

    homeActionBusy = true;

    var homeList = document.getElementById(
      "home-status-list"
    );

    if (homeList) {
      homeList.className += " home-status-busy";
    }
    var request = new XMLHttpRequest();

    request.onreadystatechange = function () {
      if (request.readyState !== 4) {
        return;
      }

      if (request.status !== 200) {
        showHomeActionError(
          homeList
        );
      }

      updateHomeStatusCard();

      var homeActionCooldown = 800;

      setTimeout(
        function () {
          homeActionBusy = false;

          if (homeList) {
            homeList.className = homeList.className.replace(
              / ?home-status-busy/g,
              ""
            );
          }
        },
        homeActionCooldown
      );
    };

    request.open(
      "POST",
      "/api/home/actions",
      true
    );

    request.setRequestHeader(
      "Content-Type",
      "application/json"
    );

    request.send(
      JSON.stringify(
        {
          entity_id: entityId,
          action: action
        }
      )
    );
  }

  function setHomeTemperature(
    entityId,
    temperature
  ) {
    if (homeActionBusy) {
      return;
    }

    homeActionBusy = true;

    var homeList = document.getElementById(
      "home-status-list"
    );

    if (homeList) {
      homeList.className += " home-status-busy";
    }

    var request = new XMLHttpRequest();

    request.onreadystatechange = function () {
      if (request.readyState !== 4) {
        return;
      }

      if (request.status !== 200) {
        showHomeActionError(
          homeList
        );
      }

      updateHomeStatusCard();

      var homeActionCooldown = 800;

      setTimeout(
        function () {
          homeActionBusy = false;

          if (homeList) {
            homeList.className = homeList.className.replace(
              / ?home-status-busy/g,
              ""
            );
          }
        },
        homeActionCooldown
      );
    };

    request.open(
      "POST",
      "/api/home/actions",
      true
    );

    request.setRequestHeader(
      "Content-Type",
      "application/json"
    );

    request.send(
      JSON.stringify(
        {
          entity_id: entityId,
          action: "set_temperature",
          temperature: temperature
        }
      )
    );
  }

  function decreaseHomeTemperature(
    entityId,
    temperature,
    target_temp_step,
    minTemp
  ) {
    var target =
      temperature - target_temp_step;

    if (target < minTemp) {
      target = minTemp;
    }

    setHomeTemperature(
      entityId,
      target
    );
  }

  function increaseHomeTemperature(
    entityId,
    temperature,
    target_temp_step,
    maxTemp
  ) {
    var target =
      temperature + target_temp_step;

    if (target > maxTemp) {
      target = maxTemp;
    }

    setHomeTemperature(
      entityId,
      target
    );
  }

  window.setHomeTemperature = setHomeTemperature;
  window.decreaseHomeTemperature =
    decreaseHomeTemperature;
  window.increaseHomeTemperature =
    increaseHomeTemperature;

  function clearHomeControlActive(
    homeList
  ) {
    if (!homeList) {
      return;
    }

    var buttons = homeList.getElementsByTagName(
      "button"
    );
    var index;

    for (
      index = 0;
      index < buttons.length;
      index += 1
    ) {
      buttons[index].className =
        buttons[index].className.replace(
          / ?home-control-active/g,
          ""
        );
    }

    if (
      homeList.className.indexOf(
        "home-control-pending"
      ) === -1
    ) {
      homeList.className +=
        " home-control-pending";
    }
  }

  function setHomeFanMode(
    entityId,
    fanMode
  ) {
    if (homeActionBusy) {
      return;
    }

    homeActionBusy = true;

    var homeList = document.getElementById(
      "home-status-list"
    );

    if (homeList) {
      homeList.className += " home-status-busy";
    }

    var request = new XMLHttpRequest();

    request.onreadystatechange = function () {
      if (request.readyState !== 4) {
        return;
      }

      if (request.status !== 200) {
        showHomeActionError(
          homeList
        );
      }

      updateHomeStatusCard();

      var homeActionCooldown = 800;

      setTimeout(
        function () {
          homeActionBusy = false;

          if (homeList) {
            homeList.className = homeList.className.replace(
              / ?home-status-busy/g,
              ""
            );
          }
        },
        homeActionCooldown
      );
    };

    request.open(
      "POST",
      "/api/home/actions",
      true
    );

    request.setRequestHeader(
      "Content-Type",
      "application/json"
    );

    request.send(
      JSON.stringify(
        {
          entity_id: entityId,
          action: "set_fan_mode",
          fan_mode: fanMode
        }
      )
    );
  }

  window.setHomeFanMode = setHomeFanMode;

  function setHomeHvacMode(
    entityId,
    hvacMode
  ) {
    if (homeActionBusy) {
      return;
    }

    homeActionBusy = true;

    var homeList = document.getElementById(
      "home-status-list"
    );

    if (homeList) {
      homeList.className += " home-status-busy";
    }

    var request = new XMLHttpRequest();

    request.onreadystatechange = function () {
      if (request.readyState !== 4) {
        return;
      }

      if (request.status !== 200) {
        showHomeActionError(
          homeList
        );
      }

      updateHomeStatusCard();

      var homeActionCooldown = 800;

      setTimeout(
        function () {
          homeActionBusy = false;

          if (homeList) {
            homeList.className = homeList.className.replace(
              / ?home-status-busy/g,
              ""
            );
          }
        },
        homeActionCooldown
      );
    };

    request.open(
      "POST",
      "/api/home/actions",
      true
    );

    request.setRequestHeader(
      "Content-Type",
      "application/json"
    );

    request.send(
      JSON.stringify(
        {
          entity_id: entityId,
          action: "set_hvac_mode",
          hvac_mode: hvacMode
        }
      )
    );
  }

  window.setHomeHvacMode = setHomeHvacMode;

  var homeCoverLastKnownState = {};

  try {
    var storedHomeCoverLastKnownState =
      localStorage.getItem(
        "smartscreen.homeCoverLastKnownState"
      );

    if (storedHomeCoverLastKnownState) {
      homeCoverLastKnownState =
        JSON.parse(
          storedHomeCoverLastKnownState
        ) || {};
    }
  } catch (error) {
    homeCoverLastKnownState = {};
  }

  function saveHomeCoverLastKnownState() {
    try {
      localStorage.setItem(
        "smartscreen.homeCoverLastKnownState",
        JSON.stringify(
          homeCoverLastKnownState
        )
      );
    } catch (error) {
      // Keep the in-memory cache when storage
      // is unavailable.
    }
  }

  var homeCoverStopFeedback = {};

  function setHomeCoverStopFeedback(
    entityId
  ) {
    homeCoverStopFeedback[entityId] = true;

    setHomeCoverPendingUi(
      entityId,
      "stop"
    );

    setTimeout(
      function () {
        delete homeCoverStopFeedback[entityId];

        setHomeCoverPendingUi(
          entityId,
          ""
        );
      },
      500
    );
  }

  function setHomeCoverPendingUi(
    entityId,
    coverAction
  ) {
    var homeList = document.getElementById(
      "home-status-list"
    );

    if (!homeList) {
      return;
    }

    var controls =
      homeList.getElementsByClassName(
        "home-cover-controls"
      );

    for (var i = 0; i < controls.length; i += 1) {
      var buttons =
        controls[i].getElementsByTagName(
          "button"
        );

      for (var j = 0; j < buttons.length; j += 1) {
        var button = buttons[j];
        var buttonEntityId =
          button.getAttribute(
            "data-cover-entity-id"
          );
        var buttonCoverAction =
          button.getAttribute(
            "data-cover-action"
          );

        if (buttonEntityId !== entityId) {
          continue;
        }

        button.className =
          buttonCoverAction === coverAction
            ? "home-control-active"
            : "";
      }
    }
  }

  function performHomeCoverAction(
    entityId,
    coverAction
  ) {
    if (homeActionBusy) {
      return;
    }

    homeActionBusy = true;

    var homeList = document.getElementById(
      "home-status-list"
    );

    var previousCoverLastAction =
      homeCoverLastAction[entityId] || "";

    if (coverAction === "stop") {
      homeCoverLastAction[entityId] = "";

      setHomeCoverStopFeedback(
        entityId
      );
    } else {
      homeCoverLastAction[entityId] = coverAction;

      setHomeCoverPendingUi(
        entityId,
        coverAction
      );

      updateHomeStatusCard();
    }

    var request = new XMLHttpRequest();

    request.onreadystatechange = function () {
      if (request.readyState !== 4) {
        return;
      }

      if (request.status !== 200) {
        homeCoverLastAction[entityId] =
          previousCoverLastAction;

        setHomeCoverPendingUi(
          entityId,
          previousCoverLastAction
        );

        showHomeActionError(
          homeList
        );

        updateHomeStatusCard();
      }

      var homeActionCooldown = 800;

      setTimeout(
        function () {
          homeActionBusy = false;
        },
        homeActionCooldown
      );
    };

    request.open(
      "POST",
      "/api/home/actions",
      true
    );

    request.setRequestHeader(
      "Content-Type",
      "application/json"
    );

    request.send(
      JSON.stringify(
        {
          entity_id: entityId,
          action: "cover_action",
          cover_action: coverAction
        }
      )
    );
  }

  window.performHomeCoverAction =
    performHomeCoverAction;

  window.performHomeAction = performHomeAction;

  function updateHomeStatusCard() {
    var request = new XMLHttpRequest();

    request.onreadystatechange = function () {
      if (request.readyState !== 4) {
        return;
      }

      var list = document.getElementById("home-status-list");

      if (request.status !== 200) {
        if (!homeStatusHasData) {
          list.innerHTML = "暂无家庭状态";
        }
        return;
      }

      var payload;

      try {
        payload = JSON.parse(request.responseText);
      } catch (error) {
        if (!homeStatusHasData) {
          list.innerHTML = "暂无家庭状态";
        }
        return;
      }

      var available = payload.available;

      if (
        payload.revision !== undefined &&
        payload.revision === homeStatusRevision &&
        available === homeStatusAvailable
      ) {
        return;
      }

      if (payload.revision !== undefined) {
        homeStatusRevision = payload.revision;
      }

      homeStatusAvailable = available;

      var items = payload.items || [];
      var html = "";

      if (payload.available === false) {
        html +=
          '<div class="home-status-offline">' +
            '<div>Home Assistant 暂时离线</div>' +
            '<div>当前显示最后一次已知状态</div>' +
          "</div>";
      }

      if (items.length === 0) {
        list.innerHTML = (
          html ||
          "暂无家庭状态"
        );

        homeStatusHasData = true;
        return;
      }

      var index;

      for (index = 0; index < items.length; index += 1) {
        var item = items[index];

        var stateClass = homeStatusClass(
          item.state
        );

        var iconClass = "";

        if (item.icon) {
          iconClass = "icon-" + item.icon;
        }

        var actionClass = "";
        var actionAttributes = "";
        var resolvedAction = item.action || "";

        var hasDedicatedClimateControls = (
          item.current_temperature !== undefined ||
          item.temperature !== undefined ||
          item.fan_mode
        );

        var hasDedicatedLightControl = (
          item.entity_id &&
          item.entity_id.indexOf(
            "light."
          ) === 0
        );

        if (
          !resolvedAction &&
          item.actions &&
          item.actions.length
        ) {
          if (
            item.raw_state === "off" &&
            item.actions.indexOf("turn_on") !== -1
          ) {
            resolvedAction = "turn_on";
          } else if (
            item.actions.indexOf("turn_off") !== -1
          ) {
            resolvedAction = "turn_off";
          }
        }

        if (
          resolvedAction &&
          !hasDedicatedClimateControls &&
          !hasDedicatedLightControl
        ) {
          actionClass = " home-status-actionable";

          actionAttributes =
            ' data-entity-id="' +
              item.entity_id +
            '"' +
            ' data-action="' +
              resolvedAction +
            '"' +
            ' onclick="performHomeAction(' +
              "'" + item.entity_id + "'," +
              "'" + resolvedAction + "'" +
            ')"';
        }

        var detailHtml = "";

        if (
          hasDedicatedLightControl &&
          resolvedAction
        ) {
          detailHtml +=
            '<div class="home-light-controls">' +
              '<button type="button" class="' +
                (
                  item.raw_state === "on"
                    ? "home-control-active"
                    : ""
                ) +
              '" onclick="event.stopPropagation();' +
                'performHomeAction(' +
                  "'" + item.entity_id + "'," +
                  "'turn_on'" +
                ');">开</button>' +
              '<button type="button" class="' +
                (
                  item.raw_state === "off"
                    ? "home-control-active"
                    : ""
                ) +
              '" onclick="event.stopPropagation();' +
                'performHomeAction(' +
                  "'" + item.entity_id + "'," +
                  "'turn_off'" +
                ');">关</button>' +
            "</div>";
        }

        if (
          item.current_temperature !== undefined ||
          item.temperature !== undefined ||
          item.fan_mode
        ) {
          var detailParts = [];

          if (item.current_temperature !== undefined) {
            detailParts.push(
              "室温 " +
              item.current_temperature +
              "°C"
            );
          }

          if (item.temperature !== undefined) {
            detailParts.push(
              "设定 " +
              item.temperature +
              "°C"
            );
          }

          if (item.fan_mode) {
            var fanModeText = item.fan_mode;

            if (item.fan_mode === "low") {
              fanModeText = "低风";
            } else if (item.fan_mode === "medium") {
              fanModeText = "中风";
            }

            detailParts.push(
              fanModeText
            );
          }

          if (detailParts.length) {
            detailHtml =
              '<div class="home-status-detail">' +
                detailParts.join(" · ") +
              "</div>";
          }

          if (
            item.entity_id &&
            item.temperature !== undefined &&
            item.target_temp_step !== undefined &&
            item.min_temp !== undefined &&
            item.max_temp !== undefined
          ) {
            detailHtml +=
              '<div class="home-temperature-controls">' +
                '<button type="button" ' +
                  'onclick="event.stopPropagation();' +
                    'decreaseHomeTemperature(' +
                      "'" + item.entity_id + "'," +
                      item.temperature + "," +
                      item.target_temp_step + "," +
                      item.min_temp +
                    ');">−</button>' +
                '<span>' +
                  item.temperature +
                  '°C' +
                '</span>' +
                '<button type="button" ' +
                  'onclick="event.stopPropagation();' +
                    'increaseHomeTemperature(' +
                      "'" + item.entity_id + "'," +
                      item.temperature + "," +
                      item.target_temp_step + "," +
                      item.max_temp +
                    ');">+</button>' +
              "</div>";
          }

          if (
            item.entity_id &&
            item.fan_mode
          ) {
            detailHtml +=
              '<div class="home-fan-controls">' +
                '<span>风速</span>' +
                '<button type="button" class="' +
                  (
                    item.fan_mode === "low"
                      ? "home-control-active"
                      : ""
                  ) +
                '" onclick="event.stopPropagation();' +
                    'setHomeFanMode(' +
                      "'" + item.entity_id + "'," +
                      "'low'" +
                    ');">2档</button>' +
                '<button type="button" class="' +
                  (
                    item.fan_mode === "medium"
                      ? "home-control-active"
                      : ""
                  ) +
                '" onclick="event.stopPropagation();' +
                    'setHomeFanMode(' +
                      "'" + item.entity_id + "'," +
                      "'medium'" +
                    ');">3档</button>' +
              "</div>";
          }

          if (item.entity_id) {
            detailHtml +=
              '<div class="home-hvac-controls">' +
                '<span>模式</span>' +
                '<button type="button" class="' +
                  (
                    item.raw_state === "off"
                      ? "home-control-active"
                      : ""
                  ) +
                '" onclick="event.stopPropagation();' +
                    'setHomeHvacMode(' +
                      "'" + item.entity_id + "'," +
                      "'off'" +
                    ');">关闭</button>' +
                '<button type="button" class="' +
                  (
                    item.raw_state === "cool"
                      ? "home-control-active"
                      : ""
                  ) +
                '" onclick="event.stopPropagation();' +
                    'setHomeHvacMode(' +
                      "'" + item.entity_id + "'," +
                      "'cool'" +
                    ');">制冷</button>' +
                '<button type="button" class="' +
                  (
                    item.raw_state === "heat"
                      ? "home-control-active"
                      : ""
                  ) +
                '" onclick="event.stopPropagation();' +
                    'setHomeHvacMode(' +
                      "'" + item.entity_id + "'," +
                      "'heat'" +
                    ');">制热</button>' +
              "</div>";
          }
        }

        if (
          item.cover_control &&
          item.entity_id
        ) {
          var coverLastAction =
            homeCoverLastAction[
              item.entity_id
            ] || "";

          var coverDisplayState = item.state;

          if (item.position !== undefined) {
            if (
              item.position === 100 &&
              coverLastAction === "open"
            ) {
              homeCoverLastAction[
                item.entity_id
              ] = "";
              coverLastAction = "";
            } else if (
              item.position === 0 &&
              coverLastAction === "close"
            ) {
              homeCoverLastAction[
                item.entity_id
              ] = "";
              coverLastAction = "";
            }

            if (
              coverLastAction === "open" &&
              item.position === 0
            ) {
              coverDisplayState = "打开中";
            } else if (
              coverLastAction === "close" &&
              item.position === 100
            ) {
              coverDisplayState = "关闭中";
            } else if (coverLastAction === "stop") {
              coverDisplayState = "已停止";
            } else if (item.position === 0) {
              coverDisplayState = "已关闭";
            } else if (item.position === 100) {
              coverDisplayState = "已打开";
            } else if (
              item.position > 0 &&
              item.position < 100
            ) {
              coverDisplayState =
                item.position + "%打开";
            }
          } else if (
            item.raw_state === "unknown" ||
            item.raw_state === "unavailable"
          ) {
            if (coverLastAction === "open") {
              coverDisplayState = "打开中";
            } else if (coverLastAction === "close") {
              coverDisplayState = "关闭中";
            } else if (coverLastAction === "stop") {
              coverDisplayState = "已停止";
            } else if (
              homeCoverLastKnownState[item.entity_id]
            ) {
              coverDisplayState =
                homeCoverLastKnownState[
                  item.entity_id
                ];
            } else {
              coverDisplayState = "状态不可用";
            }
          }

          if (
            item.raw_state !== "unknown" &&
            item.raw_state !== "unavailable"
          ) {
            homeCoverLastKnownState[item.entity_id] =
              coverDisplayState;

            saveHomeCoverLastKnownState();
          }

          item.state = coverDisplayState;

          detailHtml +=
            '<div class="home-cover-controls">' +
              '<button type="button" class="' +
                (
                  coverLastAction === "open"
                    ? "home-control-active"
                    : ""
                ) +
              '" data-cover-entity-id="' +
                item.entity_id +
              '" data-cover-action="open"' +
              ' onclick="event.stopPropagation();' +
                'performHomeCoverAction(' +
                  "'" + item.entity_id + "'," +
                  "'open'" +
                ');">打开</button>' +
              '<button type="button" class="' +
                (
                  coverLastAction === "stop" ||
                  homeCoverStopFeedback[
                    item.entity_id
                  ]
                    ? "home-control-active"
                    : ""
                ) +
              '" data-cover-entity-id="' +
                item.entity_id +
              '" data-cover-action="stop"' +
              ' onclick="event.stopPropagation();' +
                'performHomeCoverAction(' +
                  "'" + item.entity_id + "'," +
                  "'stop'" +
                ');">停止</button>' +
              '<button type="button" class="' +
                (
                  coverLastAction === "close"
                    ? "home-control-active"
                    : ""
                ) +
              '" data-cover-entity-id="' +
                item.entity_id +
              '" data-cover-action="close"' +
              ' onclick="event.stopPropagation();' +
                'performHomeCoverAction(' +
                  "'" + item.entity_id + "'," +
                  "'close'" +
                ');">关闭</button>' +
            "</div>";
        }

        html +=
          '<div class="home-status-row ' +
            stateClass +
            actionClass +
          '"' +
            actionAttributes +
          ">" +
            '<span class="home-status-icon ' +
              iconClass +
            '"></span>' +
            '<span class="home-status-name">' +
              item.name +
            "</span>" +
            '<span class="home-status-value">' +
              item.state +
            "</span>" +
            detailHtml +
          "</div>";
      }

      list.innerHTML = html;
    };

    request.open(
      "GET",
      "/api/home?ts=" + new Date().getTime(),
      true
    );
    request.send();
  }

  function updateDashboard() {
    var request = new XMLHttpRequest();

    request.onreadystatechange = function () {
      if (request.readyState !== 4) {
        return;
      }

      if (request.status !== 200) {
        showConnectionError();
        return;
      }

      var payload;

      try {
        payload = JSON.parse(request.responseText);
      } catch (error) {
        showConnectionError();
        return;
      }

      var capabilities = payload.capabilities || {};
      var clock = capabilities["session-clock-main"] || {};

      document.getElementById("time").innerHTML =
        formatClockTime(
          clock.time
        );

      document.getElementById("date").innerHTML =
        formatDate(clock.date, clock.weekday);

      renderTodaySummary(
        clock.date,
        clock.weekday
      );

      updateCalendarClock(clock.date, clock.time);
      updateTodayCalendar(
        clock.date,
        clock.weekday
      );

      setUpdateStatus(
        "fresh",
        "数据已更新"
      );
    };

    request.onerror = showConnectionError;
    request.open("GET", "/api/snapshot", true);
    request.send();
  }

  function semanticStatusNodeId(
    baseId,
    locationId
  ) {
    if (!locationId) {
      return baseId;
    }

    return (
      baseId +
      "--" +
      encodeURIComponent(locationId)
    );
  }

  function removeStaleSemanticStatusItems(
    seenSemanticNodeIds
  ) {
    var container = document.getElementById(
      "semantic-status-list"
    );

    if (!container) {
      return;
    }

    var items = container.getElementsByClassName(
      "semantic-status-item"
    );

    for (var i = items.length - 1; i >= 0; i -= 1) {
      var item = items[i];

      if (!seenSemanticNodeIds[item.id]) {
        container.removeChild(item);
      }
    }
  }

  function semanticTargetPriority(target) {
    if (target === "occupancy") {
      return 10;
    }

    if (target === "comfort") {
      return 20;
    }

    if (target === "lighting") {
      return 30;
    }

    if (target === "umbrella_advice") {
      return 40;
    }

    if (target === "clothing_advice") {
      return 50;
    }

    return 100;
  }

  function sortSemanticCards(cards) {
    return cards.slice().sort(
      function (left, right) {
        var leftOrder =
          left.location_order;
        var rightOrder =
          right.location_order;

        var leftHasOrder =
          typeof leftOrder === "number";
        var rightHasOrder =
          typeof rightOrder === "number";

        if (
          leftHasOrder &&
          rightHasOrder &&
          leftOrder !== rightOrder
        ) {
          return leftOrder - rightOrder;
        }

        if (leftHasOrder && !rightHasOrder) {
          return -1;
        }

        if (!leftHasOrder && rightHasOrder) {
          return 1;
        }

        var leftLocation =
          left.location_id || "";
        var rightLocation =
          right.location_id || "";

        if (leftLocation < rightLocation) {
          return -1;
        }

        if (leftLocation > rightLocation) {
          return 1;
        }

        var leftPriority =
          semanticTargetPriority(
            left.target
          );

        var rightPriority =
          semanticTargetPriority(
            right.target
          );

        if (leftPriority < rightPriority) {
          return -1;
        }

        if (leftPriority > rightPriority) {
          return 1;
        }

        var leftTarget =
          left.target || "";
        var rightTarget =
          right.target || "";

        if (leftTarget < rightTarget) {
          return -1;
        }

        if (leftTarget > rightTarget) {
          return 1;
        }

        return 0;
      }
    );
  }

  function renderSemanticEmptyState() {
    var container = document.getElementById(
      "semantic-status-list"
    );

    if (!container) {
      return;
    }

    var item = document.getElementById(
      "semantic-status-empty"
    );

    if (!item) {
      item = document.createElement("div");
      item.id = "semantic-status-empty";
      item.className = "semantic-status-empty";
      container.appendChild(item);
    }

    item.innerHTML = "暂无可用环境状态";
  }

  function removeSemanticEmptyState() {
    var item = document.getElementById(
      "semantic-status-empty"
    );

    if (
      item &&
      item.parentNode
    ) {
      item.parentNode.removeChild(
        item
      );
    }
  }

  function renderRoomAvailability(
    location,
    seenSemanticNodeIds
  ) {
    // Availability remains part of /api/dashboard for
    // diagnostics and future UI decisions. The normal
    // dashboard only renders semantic states that
    // actually exist.
    return;
  }

  function renderOccupancyCard(card) {
    var container = document.getElementById(
      "semantic-status-list"
    );

    if (!container || !card || !card.value) {
      return;
    }

    var state = card.value.state;
    var locationId = card.location_id;
    var locationLabel = card.location_label;
    var displayLocation =
      locationLabel || locationId;
    var label = "人员状态未知";

    if (state === "occupied") {
      label = "当前有人";
    } else if (state === "unoccupied") {
      label = "当前无人";
    }

    var nodeId = semanticStatusNodeId(
      "semantic-occupancy-status",
      locationId
    );

    var item = document.getElementById(
      nodeId
    );

    if (!item) {
      item = document.createElement("div");
      item.id = nodeId;
      item.className = "semantic-status-item";
      container.appendChild(item);
    }

    item.innerHTML =
      label +
      (
        displayLocation
          ? " · " + displayLocation
          : ""
      );
  }

  function renderLightingCard(card) {
    var container = document.getElementById(
      "semantic-status-list"
    );

    if (!container || !card || !card.value) {
      return;
    }

    var state = card.value.state;
    var locationId = card.location_id;
    var locationLabel = card.location_label;
    var displayLocation =
      locationLabel || locationId;
    var label = "光线状态未知";

    if (state === "dim") {
      label = "光线偏暗";
    } else if (state === "comfortable") {
      label = "光线适宜";
    } else if (state === "bright") {
      label = "光线较亮";
    }

    var nodeId = semanticStatusNodeId(
      "semantic-lighting-status",
      locationId
    );

    var item = document.getElementById(
      nodeId
    );

    if (!item) {
      item = document.createElement("div");
      item.id = nodeId;
      item.className = "semantic-status-item";
      container.appendChild(item);
    }

    item.innerHTML =
      label +
      (
        displayLocation
          ? " · " + displayLocation
          : ""
      );
  }

  function renderComfortCard(card) {
    var container = document.getElementById(
      "semantic-status-list"
    );

    if (!container || !card || !card.value) {
      return;
    }

    var level = card.value.level;
    var score = card.value.score;
    var locationId = card.location_id;
    var locationLabel = card.location_label;
    var displayLocation =
      locationLabel || locationId;
    var label = "舒适度未知";

    if (level === "comfortable") {
      label = "舒适";
    } else if (
      level === "slightly_uncomfortable"
    ) {
      label = "稍有不适";
    } else if (level === "uncomfortable") {
      label = "不舒适";
    }

    var nodeId = semanticStatusNodeId(
      "semantic-comfort-status",
      locationId
    );

    var item = document.getElementById(
      nodeId
    );

    if (!item) {
      item = document.createElement("div");
      item.id = nodeId;
      item.className = "semantic-status-item";
      container.appendChild(item);
    }

    item.innerHTML =
      label +
      (
        score != null
          ? " · 舒适度 " + score
          : ""
      ) +
      (
        displayLocation
          ? " · " + displayLocation
          : ""
      );
  }

  function renderUmbrellaAdviceCard(card) {
    var container = document.getElementById(
      "semantic-status-list"
    );

    if (!container || !card || !card.value) {
      return;
    }

    var locationId = card.location_id;
    var locationLabel = card.location_label;
    var displayLocation =
      locationLabel || locationId;

    var recommended =
      card.value.recommended === true;

    var label =
      recommended
        ? "建议带伞"
        : "无需带伞";

    var nodeId = semanticStatusNodeId(
      "semantic-umbrella-advice",
      locationId
    );

    var item = document.getElementById(
      nodeId
    );

    if (!item) {
      item = document.createElement("div");
      item.id = nodeId;
      item.className = "semantic-status-item";
      container.appendChild(item);
    }

    item.innerHTML =
      label +
      (
        displayLocation
          ? " · " + displayLocation
          : ""
      );
  }

  function renderClothingAdviceCard(card) {
    var container = document.getElementById(
      "semantic-status-list"
    );

    if (!container || !card || !card.value) {
      return;
    }

    var locationId = card.location_id;
    var locationLabel = card.location_label;
    var displayLocation =
      locationLabel || locationId;

    var level = card.value.level;
    var label = "穿衣建议未知";

    if (level === "warm") {
      label = "注意保暖";
    } else if (level === "light") {
      label = "轻便着装";
    } else if (level === "hot_weather") {
      label = "清凉着装";
    }

    var nodeId = semanticStatusNodeId(
      "semantic-clothing-advice",
      locationId
    );

    var item = document.getElementById(
      nodeId
    );

    if (!item) {
      item = document.createElement("div");
      item.id = nodeId;
      item.className = "semantic-status-item";
      container.appendChild(item);
    }

    item.innerHTML =
      label +
      (
        displayLocation
          ? " · " + displayLocation
          : ""
      );
  }

  function setDeviceButtonActive(
    selector,
    active
  ) {
    var panel = document.getElementById(
      "xingoo-air-purifier-controls"
    );

    if (!panel) {
      return;
    }

    var buttons = panel.querySelectorAll(
      selector
    );

    for (
      var i = 0;
      i < buttons.length;
      i += 1
    ) {
      if (active) {
        buttons[i].classList.add(
          "device-control-active"
        );
      } else {
        buttons[i].classList.remove(
          "device-control-active"
        );
      }
    }
  }


  function renderXingooDeviceControlState(
    observations
  ) {
    observations = observations || [];

    var panel = document.getElementById(
      "xingoo-air-purifier-controls"
    );

    if (!panel) {
      return;
    }

    var deviceId = panel.getAttribute(
      "data-device-id"
    );

    if (!deviceId) {
      return;
    }

    var state = {};

    for (
      var i = 0;
      i < observations.length;
      i += 1
    ) {
      var observation = observations[i];
      var provenance =
        observation.provenance || {};

      if (
        provenance.device_id
        !== deviceId
      ) {
        continue;
      }

      if (
        observation.quality
        === "unavailable"
      ) {
        continue;
      }

      state[
        observation.parameter
      ] = observation.value;
    }

    function setPurifierReading(
      parameter,
      suffix
    ) {
      var node = panel.querySelector(
        '[data-purifier-reading="' +
        parameter +
        '"]'
      );

      if (!node) {
        return;
      }

      var value = state[parameter];

      if (
        value === undefined
        ||
        value === null
      ) {
        node.textContent = "—";
        return;
      }

      node.textContent =
        String(value) + (suffix || "");
    }

    setPurifierReading(
      "temperature",
      " °C"
    );
    setPurifierReading(
      "humidity",
      " %"
    );
    setPurifierReading(
      "pm25",
      ""
    );
    setPurifierReading(
      "hcho",
      ""
    );

    var allButtons = panel.querySelectorAll(
      "[data-device-control]"
    );

    for (
      var buttonIndex = 0;
      buttonIndex < allButtons.length;
      buttonIndex += 1
    ) {
      allButtons[
        buttonIndex
      ].classList.remove(
        "device-control-active"
      );
    }

    if (state.power === true) {
      setDeviceButtonActive(
        '[data-device-control="power"]' +
        '[data-control-value="true"]',
        true
      );
    } else if (
      state.power === false
    ) {
      setDeviceButtonActive(
        '[data-device-control="power"]' +
        '[data-control-value="false"]',
        true
      );
    }

    if (state.mode === 0) {
      setDeviceButtonActive(
        '[data-device-control="mode"]' +
        '[data-control-value="smart"]',
        true
      );
    } else if (
      state.mode === 2
    ) {
      setDeviceButtonActive(
        '[data-device-control="mode"]' +
        '[data-control-value="sleep"]',
        true
      );
    }

    if (
      typeof state.wind_speed
      === "number"
    ) {
      setDeviceButtonActive(
        '[data-device-control="wind_speed"]' +
        '[data-control-value="' +
        state.wind_speed +
        '"]',
        true
      );
    }

    if (
      typeof state.ions
      === "boolean"
    ) {
      setDeviceButtonActive(
        '[data-device-control="ions"]' +
        '[data-control-value="' +
        (
          state.ions
            ? "true"
            : "false"
        ) +
        '"]',
        true
      );
    }

    if (
      typeof state.disinfection
      === "boolean"
    ) {
      setDeviceButtonActive(
        '[data-device-control="disinfection"]' +
        '[data-control-value="' +
        (
          state.disinfection
            ? "true"
            : "false"
        ) +
        '"]',
        true
      );
    }

    var effectiveScreenOn =
      state.screen_on;

    if (state.mode === 2) {
      effectiveScreenOn = false;
    }

    if (
      typeof effectiveScreenOn
      === "boolean"
    ) {
      setDeviceButtonActive(
        '[data-device-control="screen_on"]' +
        '[data-control-value="' +
        (
          effectiveScreenOn
            ? "true"
            : "false"
        ) +
        '"]',
        true
      );
    }

    if (
      typeof state.child_lock
      === "boolean"
    ) {
      setDeviceButtonActive(
        '[data-device-control="child_lock"]' +
        '[data-control-value="' +
        (
          state.child_lock
            ? "true"
            : "false"
        ) +
        '"]',
        true
      );
    }
  }



  function bindSpecialDevicePanels(
    devices
  ) {
    devices = devices || [];

    var purifierPanel =
      document.getElementById(
        "xingoo-air-purifier-controls"
      );

    if (!purifierPanel) {
      return;
    }

    purifierPanel.removeAttribute(
      "data-device-id"
    );

    var deviceType =
      purifierPanel.getAttribute(
        "data-device-type"
      );

    if (!deviceType) {
      return;
    }

    for (
      var i = 0;
      i < devices.length;
      i += 1
    ) {
      var device = devices[i];

      if (
        device.device_type
        !== deviceType
      ) {
        continue;
      }

      purifierPanel.setAttribute(
        "data-device-id",
        device.device_id
      );

      return;
    }
  }


  function deviceControlLabel(
    controlId
  ) {
    var labels = {
      power: "开关",
      brightness: "亮度",
      color_temperature: "色温",
      operating_state: "模式",
      target_temperature: "设定温度",
      fan_mode: "风速",
      state: "状态",
      position: "位置",
      clean_all: "全屋清扫",
      clean_areas: "区域清扫",
      return_to_dock: "回基站",
      mode: "模式",
      wind_speed: "风速",
      ions: "负离子",
      disinfection: "消毒",
      screen_on: "屏幕",
      child_lock: "童锁"
    };

    return (
      labels[controlId]
      || controlId
      || ""
    );
  }


  function deviceControlOptionLabel(
    controlId,
    value
  ) {
    var labels = {
      mode: {
        smart: "智能",
        sleep: "睡眠"
      },
      operating_state: {
        off: "关闭",
        cool: "制冷",
        heat: "制热"
      },
      fan_mode: {
        low: "低速",
        medium: "中速"
      },
      state: {
        open: "打开",
        close: "关闭",
        closed: "关闭",
        stop: "停止",
        stopped: "停止"
      },
      clean_areas: {
        living: "客厅",
        dining: "餐厅",
        master_bedroom: "主卧",
        princess_room: "公主房",
        study: "书房",
        master_bath: "主卫",
        guest_bath: "客卫"
      }
    };

    var controlLabels =
      labels[controlId];

    if (
      controlLabels
      && Object.prototype.hasOwnProperty.call(
        controlLabels,
        value
      )
    ) {
      return controlLabels[value];
    }

    return String(value);
  }


  function deviceControlNumberUnit(
    controlId
  ) {
    if (
      controlId === "brightness"
      || controlId === "position"
    ) {
      return " %";
    }

    if (
      controlId === "color_temperature"
    ) {
      return " K";
    }

    if (
      controlId === "target_temperature"
    ) {
      return " °C";
    }

    return "";
  }


  function renderGenericDeviceControls(
    devices,
    deviceStates
  ) {
    var container = document.getElementById(
      "generic-device-controls"
    );

    if (!container) {
      return;
    }

    devices = devices || [];
    deviceStates = deviceStates || [];

    var html = "";

    for (
      var i = 0;
      i < devices.length;
      i += 1
    ) {
      var device = devices[i];

      if (
        device.device_type === "air_purifier"
      ) {
        continue;
      }

      var controls = (
        device.controls || []
      );

      if (!controls.length) {
        continue;
      }

      var deviceState = {};

      for (
        var stateIndex = 0;
        stateIndex < deviceStates.length;
        stateIndex += 1
      ) {
        var state =
          deviceStates[
            stateIndex
          ];

        if (
          state.device_id !== device.device_id
        ) {
          continue;
        }

        if (
          state.available !== true
        ) {
          continue;
        }

        deviceState[state.parameter] = state.value;
      }

      var availabilityHtml = "";

      if (
        device.availability_reason
        === "powered_off_by_upstream"
      ) {
        continue;
      } else {
        var hasConfirmedControlState = false;

        for (
          var stateControlIndex = 0;
          stateControlIndex < controls.length;
          stateControlIndex += 1
        ) {
          var stateControl =
            controls[stateControlIndex];

          if (
            deviceState[
              stateControl.parameter
            ] !== undefined
          ) {
            hasConfirmedControlState = true;
            break;
          }
        }

        if (!hasConfirmedControlState) {
          availabilityHtml =
            '<div class="device-control-state-note">' +
            "状态未知" +
            "</div>";
        }
      }

      html +=
        '<div class="device-control-section"' +
        ' data-device-id="' +
        escapeHtml(
          device.device_id || ""
        ) +
        '">' +
        '<div class="device-control-title">' +
        escapeHtml(
          device.name ||
          device.device_id ||
          "设备"
        ) +
        "</div>" +
        availabilityHtml;

      for (
        var controlIndex = 0;
        controlIndex < controls.length;
        controlIndex += 1
      ) {
        var control =
          controls[controlIndex];

        if (
          control.kind === "boolean"
        ) {
          html +=
            '<div class="device-control-group">' +
            '<div class="device-control-label">' +
            escapeHtml(
              deviceControlLabel(
                control.control_id
              )
            ) +
            "</div>" +
            '<div class="device-control-buttons">' +
            '<button type="button"' +
            ' data-device-control="' +
            escapeHtml(
              control.control_id || ""
            ) +
            '"' +
            ' data-control-value="true"' +
            (
              deviceState[
                control.parameter
              ] === true
                ? ' class="device-control-active"'
                : ""
            ) +
            ">开</button>" +
            '<button type="button"' +
            ' data-device-control="' +
            escapeHtml(
              control.control_id || ""
            ) +
            '"' +
            ' data-control-value="false"' +
            (
              deviceState[
                control.parameter
              ] === false
                ? ' class="device-control-active"'
                : ""
            ) +
            ">关</button>" +
            "</div>" +
            "</div>";
        } else if (
          control.kind === "number"
        ) {
          var numberStateValue =
            deviceState[
              control.parameter
            ];

          var numberStateAvailable = (
            typeof numberStateValue
            === "number"
            &&
            isFinite(
              numberStateValue
            )
          );

          var numberIncrement = (
            control.step !== undefined
            && control.step !== null
              ? Number(control.step)
              : 1
          );

          if (
            control.control_id
            === "brightness"
          ) {
            numberIncrement = 5;
          } else if (
            control.control_id
            === "color_temperature"
          ) {
            numberIncrement = 100;
          } else if (
            control.control_id
            === "position"
          ) {
            numberIncrement = 10;
          }

          var numberUnit =
            deviceControlNumberUnit(
              control.control_id
            );

          var numberDisplayValue = (
            numberStateAvailable
              ? String(
                  numberStateValue
                ) + numberUnit
              : ""
          );

          html +=
            '<div class="device-control-group">' +
            '<div class="device-control-label">' +
            escapeHtml(
              deviceControlLabel(
                control.control_id
              )
            ) +
            "</div>" +
            '<div class="device-control-buttons">' +
            '<button type="button"' +
            ' data-device-control="' +
            escapeHtml(
              control.control_id || ""
            ) +
            '"' +
            ' data-control-delta="' +
            escapeHtml(
              String(
                -numberIncrement
              )
            ) +
            '"' +
            (
              numberStateAvailable ? "" : " disabled"
            ) +
            ">−</button>" +
            '<button type="button" disabled>' +
            escapeHtml(
              numberStateAvailable
                ? numberDisplayValue
                : "状态未知"
            ) +
            "</button>" +
            '<button type="button"' +
            ' data-device-control="' +
            escapeHtml(
              control.control_id || ""
            ) +
            '"' +
            ' data-control-delta="' +
            escapeHtml(
              String(
                numberIncrement
              )
            ) +
            '"' +
            (
              numberStateAvailable ? "" : " disabled"
            ) +
            ">+</button>" +
            "</div>" +
            "</div>";
        } else if (
          control.kind === "select"
        ) {
          var selectOptions = (
            control.options || []
          ).slice();

          if (
            control.control_id === "state"
          ) {
            var preferredStateOrder = [
              "open",
              "stop",
              "stopped",
              "close",
              "closed"
            ];

            selectOptions.sort(
              function (left, right) {
                var leftIndex =
                  preferredStateOrder.indexOf(
                    String(left)
                  );

                var rightIndex =
                  preferredStateOrder.indexOf(
                    String(right)
                  );

                if (leftIndex < 0) {
                  leftIndex = 100;
                }

                if (rightIndex < 0) {
                  rightIndex = 100;
                }

                return leftIndex - rightIndex;
              }
            );
          }

          var selectStateValue =
            deviceState[
              control.parameter
            ];

          html +=
            '<div class="device-control-group">' +
            '<div class="device-control-label">' +
            escapeHtml(
              deviceControlLabel(
                control.control_id
              )
            ) +
            "</div>" +
            '<div class="device-control-buttons">';

          for (
            var optionIndex = 0;
            optionIndex < selectOptions.length;
            optionIndex += 1
          ) {
            var optionValue =
              selectOptions[optionIndex];

            html +=
              '<button type="button"' +
              ' data-device-control="' +
              escapeHtml(
                control.control_id || ""
              ) +
              '"' +
              ' data-control-value="' +
              escapeHtml(
                String(optionValue)
              ) +
              '"' +
              (
                String(selectStateValue)
                === String(optionValue)
                  ? ' class="device-control-active"'
                  : ""
              ) +
              ">" +
              escapeHtml(
                deviceControlOptionLabel(
                  control.control_id,
                  String(optionValue)
                )
              ) +
              "</button>";
          }

          html +=
            "</div>" +
            "</div>";
        }
      }

      html += "</div>";
    }

    container.innerHTML = html;

    container.onclick = function (
      event
    ) {
      event = event || window.event;

      var target = (
        event.target ||
        event.srcElement
      );

      if (
        !target ||
        target.tagName !== "BUTTON"
      ) {
        return;
      }

      if (deviceControlRequestPending) {
        return;
      }

      var panel = target;

      while (
        panel &&
        panel !== container &&
        !panel.getAttribute(
          "data-device-id"
        )
      ) {
        panel = panel.parentNode;
      }

      if (
        !panel ||
        panel === container
      ) {
        return;
      }

      var deviceId = panel.getAttribute(
        "data-device-id"
      );

      var controlId = target.getAttribute(
        "data-device-control"
      );

      var rawValue = target.getAttribute(
        "data-control-value"
      );

      var rawDelta = target.getAttribute(
        "data-control-delta"
      );

      if (
        !deviceId ||
        !controlId
      ) {
        return;
      }

      var value;

      if (rawDelta !== null) {
        var matchingControl = null;

        for (
          var controlLookupIndex = 0;
          controlLookupIndex
          < controls.length;
          controlLookupIndex += 1
        ) {
          if (
            controls[
              controlLookupIndex
            ].control_id
            === controlId
          ) {
            matchingControl =
              controls[
                controlLookupIndex
              ];
            break;
          }
        }

        if (!matchingControl) {
          return;
        }

        var currentNumber = parseFloat(
          deviceState[
            matchingControl.parameter
          ]
        );

        var numberDelta = parseFloat(
          rawDelta
        );

        if (
          Number.isNaN(currentNumber)
          ||
          Number.isNaN(numberDelta)
        ) {
          return;
        }

        value =
          currentNumber
          + numberDelta;

        var controlMinimum = (
          matchingControl.min
        );

        var controlMaximum = (
          matchingControl.max
        );

        if (
          typeof controlMinimum
          === "number"
        ) {
          value = Math.max(
            controlMinimum,
            value
          );
        }

        if (
          typeof controlMaximum
          === "number"
        ) {
          value = Math.min(
            controlMaximum,
            value
          );
        }
      } else {
        if (rawValue === null) {
          return;
        }

        value = rawValue;

        if (rawValue === "true") {
          value = true;
        } else if (
          rawValue === "false"
        ) {
          value = false;
        }
      }

      sendDeviceControl(
        deviceId,
        controlId,
        value,
        target
      );
    };
  }


  function renderGenericObservations(
    observations
  ) {
    var container = document.getElementById(
      "observation-status-list"
    );

    if (!container) {
      return;
    }

    observations = observations || [];

    var visible = [];

    for (
      var i = 0;
      i < observations.length;
      i += 1
    ) {
      var item = observations[i];
      var parameter = item.parameter;

      if (
        parameter !== "illuminance" &&
        parameter !== "motion_idle_seconds" &&
        parameter !== "temperature" &&
        parameter !== "humidity" &&
        parameter !== "pm25" &&
        parameter !== "hcho"
      ) {
        continue;
      }

      visible.push(item);
    }

    visible.sort(
      function (left, right) {
        var leftOrder =
          typeof left.location_order === "number"
            ? left.location_order
            : 999999;

        var rightOrder =
          typeof right.location_order === "number"
            ? right.location_order
            : 999999;

        if (leftOrder !== rightOrder) {
          return leftOrder - rightOrder;
        }

        var leftLocation =
          left.location_id || "";

        var rightLocation =
          right.location_id || "";

        if (leftLocation < rightLocation) {
          return -1;
        }

        if (leftLocation > rightLocation) {
          return 1;
        }

        var leftParameter =
          left.parameter || "";

        var rightParameter =
          right.parameter || "";

        if (leftParameter < rightParameter) {
          return -1;
        }

        if (leftParameter > rightParameter) {
          return 1;
        }

        return 0;
      }
    );

    if (visible.length === 0) {
      container.innerHTML =
        '<div class="observation-status-empty">' +
        "暂无传感器数据" +
        "</div>";

      return;
    }

    var html = "";

    for (
      var visibleIndex = 0;
      visibleIndex < visible.length;
      visibleIndex += 1
    ) {
      var observation = visible[visibleIndex];
      var parameterName = observation.parameter;

      var locationLabel =
        observation.location_label ||
        observation.location_id ||
        "未知位置";

      var label = parameterName;
      var value = observation.value;
      var unit = observation.unit || "";

      if (parameterName === "illuminance") {
        label = "光照度";
      } else if (
        parameterName === "motion_idle_seconds"
      ) {
        label = "无移动持续";
        unit = "秒";
      } else if (
        parameterName === "temperature"
      ) {
        label = "温度";

        if (unit === "degC") {
          unit = "°C";
        }
      } else if (
        parameterName === "humidity"
      ) {
        label = "湿度";

        if (unit === "percent") {
          unit = "%";
        }
      } else if (
        parameterName === "pm25"
      ) {
        label = "PM2.5";
      } else if (
        parameterName === "hcho"
      ) {
        label = "甲醛";
      }

      html +=
        '<div class="observation-status-row">' +
          '<span class="observation-status-location">' +
            locationLabel +
          "</span>" +
          '<span class="observation-status-name">' +
            label +
          "</span>" +
          '<span class="observation-status-value">' +
            value +
            (
              unit
                ? " " + unit
                : ""
            ) +
          "</span>" +
        "</div>";
    }

    container.innerHTML = html;
  }


  function renderFamilySummary(
    cards,
    zones,
    deviceStates,
    devices
  ) {
    var reminder = document.getElementById(
      "reminder-list"
    );

    if (!reminder) {
      return;
    }

    cards = cards || [];
    zones = zones || [];
    deviceStates = deviceStates || [];
    devices = devices || [];

    var hasIndoorComfort = false;
    var hasComfortConcern = false;
    var attentionParts = [];
    var doorAttentionParts = [];
    var occupancyByLocation = {};

    var index;

    for (
      index = 0;
      index < cards.length;
      index += 1
    ) {
      var occupancyCard = cards[index];

      if (
        !occupancyCard ||
        !occupancyCard.value ||
        !occupancyCard.location_id ||
        occupancyCard.target !== "occupancy"
      ) {
        continue;
      }

      occupancyByLocation[
        occupancyCard.location_id
      ] = occupancyCard.value.state;
    }

    for (
      index = 0;
      index < cards.length;
      index += 1
    ) {
      var card = cards[index];

      if (
        !card ||
        !card.value ||
        !card.location_id
      ) {
        continue;
      }

      if (card.location_id === "outdoor") {
        continue;
      }

      var location =
        card.location_label ||
        card.location_id;

      if (
        card.target === "comfort"
      ) {
        hasIndoorComfort = true;

        if (
          card.value.level &&
          card.value.level !== "comfortable"
        ) {
          hasComfortConcern = true;
        }
      }

      if (
        card.target !== "lighting" ||
        card.value.state !== "dim"
      ) {
        continue;
      }

      var occupancyLocationId =
        card.location_id;

      for (
        var zoneIndex = 0;
        zoneIndex < zones.length;
        zoneIndex += 1
      ) {
        var zone = zones[zoneIndex];

        if (
          !zone ||
          zone.show_on_home !== true
        ) {
          continue;
        }

        var roomIds =
          zone.room_ids || [];

        if (
          roomIds.indexOf(
            card.location_id
          ) === -1
        ) {
          continue;
        }

        if (
          zone.summary_location_id
        ) {
          occupancyLocationId =
            zone.summary_location_id;
        }

        break;
      }

      if (
        occupancyByLocation[
          occupancyLocationId
        ] === "occupied"
      ) {
        attentionParts.push(
          location + "光线偏暗"
        );
      }
    }

    /*
     * Device reminder projection.
     *
     * This remains a dashboard presentation concern:
     * Device Data owns the observed state; the home
     * dashboard decides which states deserve attention.
     */
    var deviceNameById = {};

    for (
      index = 0;
      index < devices.length;
      index += 1
    ) {
      var device = devices[index];

      if (
        !device ||
        !device.device_id
      ) {
        continue;
      }

      deviceNameById[
        device.device_id
      ] = (
        device.name ||
        device.device_id
      );
    }

    for (
      index = 0;
      index < deviceStates.length;
      index += 1
    ) {
      var state = deviceStates[index];

      if (
        !state ||
        !state.device_id ||
        !state.parameter ||
        state.available !== true
      ) {
        continue;
      }

      if (
        state.parameter === "open" &&
        state.value === true
      ) {
        if (
          state.device_id ===
            "living.entry_door_sensor_1"
        ) {
          doorAttentionParts.push(
            "入户门未关闭"
          );
          continue;
        }

        if (
          state.device_id ===
            "princess_room.fire_door_sensor_1"
        ) {
          doorAttentionParts.push(
            "公主房消防门未关闭"
          );
          continue;
        }
      }

      if (
        state.parameter ===
          "battery_level"
      ) {
        var numericBattery =
          Number(state.value);

        if (
          isFinite(numericBattery) &&
          numericBattery < 5
        ) {
          var batteryName =
            deviceNameById[
              state.device_id
            ] || state.device_id;

          attentionParts.push(
            batteryName +
            " 电量仅 " +
            String(
              Math.round(
                numericBattery
              )
            ) +
            "%"
          );
        }

        continue;
      }

      if (
        state.device_id !==
          "vacuum_001"
      ) {
        continue;
      }

      if (
        state.parameter ===
          "water_shortage" &&
        state.value === true
      ) {
        attentionParts.push(
          "扫地机器人缺水"
        );
        continue;
      }

      if (
        state.parameter ===
          "clean_water_box_problem" &&
        state.value === true
      ) {
        attentionParts.push(
          "请检查扫地机器人清水箱"
        );
        continue;
      }

      if (
        state.parameter ===
          "dirty_water_box_problem" &&
        state.value === true
      ) {
        attentionParts.push(
          "请检查扫地机器人污水箱"
        );
        continue;
      }

      if (
        state.parameter ===
          "vacuum_error" &&
        state.value !== null &&
        state.value !== undefined &&
        state.value !== "" &&
        state.value !== "none"
      ) {
        attentionParts.push(
          "扫地机器人异常：" +
          String(state.value)
        );
        continue;
      }

      if (
        state.parameter ===
          "dock_error" &&
        state.value !== null &&
        state.value !== undefined &&
        state.value !== "" &&
        state.value !== "ok"
      ) {
        attentionParts.push(
          "扫地机器人基站异常：" +
          String(state.value)
        );
      }
    }

    if (hasComfortConcern) {
      attentionParts.unshift(
        "部分区域舒适度需要留意"
      );
    }

    if (doorAttentionParts.length > 0) {
      attentionParts =
        doorAttentionParts.concat(
          attentionParts
        );
    }

    if (attentionParts.length > 0) {
      reminder.innerHTML =
        attentionParts.join(" · ");
    } else {
      reminder.innerHTML =
        "暂无需要处理的事项";
    }
  }


  function resolveAreaLocationIds(
    locationId,
    zones
  ) {
    var locationIds = [locationId];

    zones = zones || [];

    for (
      var zoneIndex = 0;
      zoneIndex < zones.length;
      zoneIndex += 1
    ) {
      var zone = zones[zoneIndex];

      if (
        !zone ||
        zone.zone_id !== locationId
      ) {
        continue;
      }

      var roomIds = zone.room_ids || [];

      for (
        var roomIndex = 0;
        roomIndex < roomIds.length;
        roomIndex += 1
      ) {
        var roomId = roomIds[roomIndex];

        if (!roomId) {
          continue;
        }

        if (
          locationIds.indexOf(roomId) === -1
        ) {
          locationIds.push(roomId);
        }
      }

      break;
    }

    return locationIds;
  }


  function resolveAreaZone(
    locationId,
    zones
  ) {
    zones = zones || [];

    for (
      var zoneIndex = 0;
      zoneIndex < zones.length;
      zoneIndex += 1
    ) {
      var zone = zones[zoneIndex];

      if (
        zone
        &&
        zone.zone_id === locationId
      ) {
        return zone;
      }
    }

    return null;
  }


  function areaSheetOrderedDevices(
    zone,
    devices
  ) {
    devices = devices || [];

    if (
      !zone
      ||
      !zone.sheet_device_order
      ||
      !zone.sheet_device_order.length
    ) {
      return devices.slice();
    }

    var configuredOrder = {};

    for (
      var orderIndex = 0;
      orderIndex
        < zone.sheet_device_order.length;
      orderIndex += 1
    ) {
      var deviceId =
        zone.sheet_device_order[
          orderIndex
        ];

      if (
        deviceId
        &&
        !Object.prototype
          .hasOwnProperty.call(
            configuredOrder,
            deviceId
          )
      ) {
        configuredOrder[
          deviceId
        ] = orderIndex;
      }
    }

    var indexedDevices =
      devices.map(
        function (
          device,
          originalIndex
        ) {
          return {
            device: device,
            originalIndex:
              originalIndex
          };
        }
      );

    indexedDevices.sort(
      function (left, right) {
        var leftId = (
          left.device
          &&
          left.device.device_id
        );

        var rightId = (
          right.device
          &&
          right.device.device_id
        );

        var leftConfigured =
          Object.prototype
            .hasOwnProperty.call(
              configuredOrder,
              leftId
            );

        var rightConfigured =
          Object.prototype
            .hasOwnProperty.call(
              configuredOrder,
              rightId
            );

        if (
          leftConfigured
          &&
          rightConfigured
        ) {
          return (
            configuredOrder[leftId]
            -
            configuredOrder[rightId]
          );
        }

        if (leftConfigured) {
          return -1;
        }

        if (rightConfigured) {
          return 1;
        }

        return (
          left.originalIndex
          -
          right.originalIndex
        );
      }
    );

    return indexedDevices.map(
      function (entry) {
        return entry.device;
      }
    );
  }


  function areaSheetWideDeviceMap(
    zone
  ) {
    var result = {};

    if (
      !zone
      ||
      !zone.sheet_wide_device_ids
    ) {
      return result;
    }

    for (
      var index = 0;
      index
        < zone.sheet_wide_device_ids.length;
      index += 1
    ) {
      var deviceId =
        zone.sheet_wide_device_ids[
          index
        ];

      if (deviceId) {
        result[deviceId] = true;
      }
    }

    return result;
  }


  function areaLocationLabel(
    locationId,
    locations
  ) {
    locations = locations || [];

    for (
      var i = 0;
      i < locations.length;
      i += 1
    ) {
      var location = locations[i];

      if (
        location &&
        location.location_id === locationId
      ) {
        return (
          location.location_label ||
          locationId
        );
      }
    }

    return locationId || "";
  }


  function closeAreaSheet() {
    var sheet = document.getElementById(
      "area-sheet"
    );

    if (!sheet) {
      return;
    }

    sheet.className = "area-sheet";
    sheet.setAttribute(
      "aria-hidden",
      "true"
    );

    activeAreaLocationId = null;
  }


  function collapseAreaSheetPowerGroups(
    container,
    devices,
    deviceStates
  ) {
    if (!container) {
      return;
    }

    devices = devices || [];
    deviceStates = deviceStates || [];

    var deviceById = {};
    var groupsByUpstream = {};

    for (
      var deviceIndex = 0;
      deviceIndex < devices.length;
      deviceIndex += 1
    ) {
      var device = devices[deviceIndex];

      if (!device) {
        continue;
      }

      deviceById[
        device.device_id
      ] = device;

      var upstreamId =
        device.power_source_device_id;

      if (!upstreamId) {
        continue;
      }

      if (
        !groupsByUpstream[
          upstreamId
        ]
      ) {
        groupsByUpstream[
          upstreamId
        ] = [];
      }

      groupsByUpstream[
        upstreamId
      ].push(device);
    }

    var renderedNodes = (
      container.getElementsByClassName(
        "area-sheet-device"
      )
    );

    var nodeByDeviceId = {};

    for (
      var nodeIndex = 0;
      nodeIndex < renderedNodes.length;
      nodeIndex += 1
    ) {
      var renderedNode =
        renderedNodes[nodeIndex];

      var renderedDeviceId =
        renderedNode.getAttribute(
          "data-device-id"
        );

      if (renderedDeviceId) {
        nodeByDeviceId[
          renderedDeviceId
        ] = renderedNode;
      }
    }

    for (
      var upstreamId
      in groupsByUpstream
    ) {
      if (
        !Object.prototype.hasOwnProperty.call(
          groupsByUpstream,
          upstreamId
        )
      ) {
        continue;
      }

      var children =
        groupsByUpstream[
          upstreamId
        ];

      if (children.length < 2) {
        continue;
      }

      var allInactive = true;

      for (
        var childIndex = 0;
        childIndex < children.length;
        childIndex += 1
      ) {
        var child =
          children[childIndex];

        if (
          child.availability_reason ===
          "powered_off_by_upstream"
        ) {
          continue;
        }

        var confirmedPowerOff = false;

        for (
          var stateIndex = 0;
          stateIndex < deviceStates.length;
          stateIndex += 1
        ) {
          var state =
            deviceStates[stateIndex];

          if (
            !state
            ||
            state.device_id !==
              child.device_id
            ||
            state.parameter !==
              "power"
            ||
            state.available !== true
          ) {
            continue;
          }

          if (state.value === false) {
            confirmedPowerOff = true;
          }

          break;
        }

        if (!confirmedPowerOff) {
          allInactive = false;
          break;
        }
      }

      if (!allInactive) {
        continue;
      }

      var childNodes = [];

      for (
        var childNodeIndex = 0;
        childNodeIndex < children.length;
        childNodeIndex += 1
      ) {
        var childNode =
          nodeByDeviceId[
            children[
              childNodeIndex
            ].device_id
          ];

        if (childNode) {
          childNodes.push(
            childNode
          );
        }
      }

      if (childNodes.length < 2) {
        continue;
      }

      for (
        var hideIndex = 0;
        hideIndex < childNodes.length;
        hideIndex += 1
      ) {
        var hiddenNode =
          childNodes[hideIndex];

        if (
          hiddenNode
          &&
          hiddenNode.parentNode
        ) {
          hiddenNode.parentNode.removeChild(
            hiddenNode
          );
        }
      }
    }
  }


  function areaSheetTitleLabel(
    locationId,
    locations
  ) {
    return areaLocationLabel(
      locationId,
      locations
    );
  }




  /*
   * Area Sheet device icon presentation.
   *
   * Presentation only.
   * Do not promote these inferred visual categories into
   * Device Data identity or control semantics.
   */
  function areaSheetDeviceVisualType(
    device,
    deviceState
  ) {
    device = device || {};
    deviceState = deviceState || {};

    if (
      device.device_type === "air_purifier"
    ) {
      return "purifier";
    }

    if (
      device.device_type === "light"
    ) {
      return "light";
    }

    var controls =
      device.controls || [];

    var controlMap = {};

    for (
      var controlIndex = 0;
      controlIndex < controls.length;
      controlIndex += 1
    ) {
      var control = controls[controlIndex];

      if (
        control
        &&
        control.control_id
      ) {
        controlMap[
          control.control_id
        ] = control;
      }
    }

    if (
      controlMap.target_temperature
      ||
      (
        controlMap.operating_state
        &&
        controlMap.fan_mode
      )
    ) {
      return "climate";
    }

    if (
      controlMap.state
      &&
      controlMap.state.kind === "select"
    ) {
      var stateOptions =
        controlMap.state.options || [];

      if (
        stateOptions.indexOf("open") >= 0
        &&
        (
          stateOptions.indexOf("closed") >= 0
          ||
          stateOptions.indexOf("close") >= 0
        )
      ) {
        return "curtain";
      }
    }

    if (
      device.area_readonly === true
      &&
      Object.prototype.hasOwnProperty.call(
        deviceState,
        "open"
      )
    ) {
      return "door";
    }

    if (
      device.area_readonly === true
      &&
      Object.prototype.hasOwnProperty.call(
        deviceState,
        "temperature"
      )
      &&
      Object.prototype.hasOwnProperty.call(
        deviceState,
        "humidity"
      )
    ) {
      return "environment";
    }

    if (
      device.area_readonly === true
      &&
      Object.prototype.hasOwnProperty.call(
        deviceState,
        "motion"
      )
      &&
      Object.prototype.hasOwnProperty.call(
        deviceState,
        "operating_state"
      )
    ) {
      return "doorbell";
    }

    return "device";
  }


  function areaSheetDeviceIconSvg(
    visualType
  ) {
    var icons = {
      light:
        '<svg viewBox="0 0 24 24"' +
        ' aria-hidden="true">' +
        '<path d="M9 18h6"/>' +
        '<path d="M10 21h4"/>' +
        '<path d="M8.6 14.7C7.6 13.8 7 12.5 7 11' +
        'a5 5 0 0 1 10 0c0 1.5-.6 2.8-1.6 3.7' +
        'C14.5 15.5 14 16.3 14 17h-4' +
        'c0-.7-.5-1.5-1.4-2.3z"/>' +
        '</svg>',

      climate:
        '<svg viewBox="0 0 24 24"' +
        ' aria-hidden="true">' +
        '<rect x="3" y="5" width="18" height="12"' +
        ' rx="2"/>' +
        '<path d="M7 9h10"/>' +
        '<path d="M8 14c1.1-1 2.2-1 3.3 0' +
        's2.2 1 3.3 0"/>' +
        '</svg>',

      curtain:
        '<svg viewBox="0 0 24 24"' +
        ' aria-hidden="true">' +
        '<path d="M4 4h16"/>' +
        '<path d="M6 5v15"/>' +
        '<path d="M18 5v15"/>' +
        '<path d="M6 5c3 2.5 3 9 0 15"/>' +
        '<path d="M18 5c-3 2.5-3 9 0 15"/>' +
        '</svg>',

      purifier:
        '<svg viewBox="0 0 24 24"' +
        ' aria-hidden="true">' +
        '<rect x="5" y="3" width="14" height="18"' +
        ' rx="3"/>' +
        '<circle cx="12" cy="12" r="4"/>' +
        '<path d="M12 8v8M8 12h8"/>' +
        '</svg>',

      door:
        '<svg viewBox="0 0 24 24"' +
        ' aria-hidden="true">' +
        '<path d="M5 21h14"/>' +
        '<path d="M7 21V4l10-1v18"/>' +
        '<circle cx="14.5" cy="12" r=".7"/>' +
        '</svg>',

      environment:
        '<svg viewBox="0 0 24 24"' +
        ' aria-hidden="true">' +
        '<path d="M9 5a2 2 0 0 1 4 0v8.2' +
        'a4 4 0 1 1-4 0z"/>' +
        '<path d="M11 8v7"/>' +
        '<path d="M16 7c1.5 1.7 2.2 3.2 2.2 4.4' +
        'A2.2 2.2 0 0 1 16 13.6"/>' +
        '</svg>',

      doorbell:
        '<svg viewBox="0 0 24 24"' +
        ' aria-hidden="true">' +
        '<path d="M6 17h12l-1.5-2v-4' +
        'a4.5 4.5 0 0 0-9 0v4z"/>' +
        '<path d="M10 20h4"/>' +
        '<path d="M12 5V3"/>' +
        '</svg>',

      device:
        '<svg viewBox="0 0 24 24"' +
        ' aria-hidden="true">' +
        '<rect x="5" y="5" width="14" height="14"' +
        ' rx="3"/>' +
        '<circle cx="12" cy="12" r="2"/>' +
        '</svg>'
    };

    return (
      icons[visualType]
      ||
      icons.device
    );
  }


  /*
   * HA-inspired light state glyph.
   *
   * Presentation only.  The boolean state already exists in
   * Device Data; this helper only chooses the visual glyph.
   *
   * on  -> illuminated bulb with rays
   * off -> bulb with diagonal slash
   */
  function areaSheetLightStateIconSvg(
    isOn
  ) {
    /*
     * Light-state glyph.
     *
     * ON and OFF deliberately share EXACTLY the same bulb
     * and base geometry.
     *
     * ON  = bulb + base + rays
     * OFF = bulb + base + slash
     *
     * This guarantees that switching state cannot change
     * the apparent bulb size or position.
     */
    var bulb =
      '<path class="area-sheet-light-bulb-fill"' +
      ' d="M7.6 10.3' +
      'a4.4 4.4 0 1 1 8.8 0' +
      'c0 1.7-.7 2.9-1.8 3.95' +
      'C13.75 15.05 13.4 15.7 13.4 16.5' +
      'h-2.8' +
      'c0-.8-.35-1.45-1.2-2.25' +
      'C8.3 13.2 7.6 12 7.6 10.3z"/>';

    var base =
      '<path class="area-sheet-light-base"' +
      ' d="M9.7 18.5h4.6' +
      'M10.5 20.7h3"/>';

    if (isOn === true) {
      return (
        '<svg viewBox="0 0 24 24"' +
        ' aria-hidden="true"' +
        ' class="area-sheet-light-state-svg' +
        ' area-sheet-light-state-svg-on">' +

        bulb +
        base +

        '<path class="area-sheet-light-rays"' +
        ' d="M12 1.4v2.1' +
        'M5.55 4.1l1.5 1.5' +
        'M18.45 4.1l-1.5 1.5' +
        'M3.35 10.4h2.15' +
        'M20.65 10.4H18.5"/>' +

        '</svg>'
      );
    }

    return (
      '<svg viewBox="0 0 24 24"' +
      ' aria-hidden="true"' +
      ' class="area-sheet-light-state-svg' +
      ' area-sheet-light-state-svg-off">' +

      bulb +
      base +

      '</svg>'
    );
  }


  function areaSheetDeviceIconHtml(
    device,
    deviceState
  ) {
    var visualType =
      areaSheetDeviceVisualType(
        device,
        deviceState
      );

    var deviceIconSvg =
      deviceIconSvg;

    if (
      visualType === "light"
      &&
      deviceState
      &&
      Object.prototype.hasOwnProperty.call(
        deviceState,
        "power"
      )
    ) {
      deviceIconSvg =
        areaSheetLightStateIconSvg(
          deviceState.power === true
        );
    }

    return (
      '<span class="area-sheet-device-icon' +
      ' area-sheet-device-icon-' +
      escapeHtml(visualType) +
      '">' +
      (
        deviceIconSvg
        ||
        areaSheetDeviceIconSvg(
          visualType
        )
      ) +
      '</span>'
    );
  }


  function renderAreaSheet(
    locationId,
    zones,
    devices,
    deviceStates,
    locations
  ) {
    var sheet = document.getElementById(
      "area-sheet"
    );
    var title = document.getElementById(
      "area-sheet-title"
    );
    var content = document.getElementById(
      "area-sheet-content"
    );

    if (
      !sheet ||
      !title ||
      !content
    ) {
      return;
    }

    zones = zones || [];
    devices = devices || [];
    deviceStates = deviceStates || [];
    locations = locations || [];

    var locationIds =
      resolveAreaLocationIds(
        locationId,
        zones
      );

    var areaZone =
      resolveAreaZone(
        locationId,
        zones
      );

    var renderDevices =
      areaSheetOrderedDevices(
        areaZone,
        devices
      );

    var wideDeviceIds =
      areaSheetWideDeviceMap(
        areaZone
      );

    var extraDeviceIds = {};

    if (
      areaZone
      &&
      areaZone.sheet_extra_device_ids
    ) {
      for (
        var extraIndex = 0;
        extraIndex
          < areaZone.sheet_extra_device_ids.length;
        extraIndex += 1
      ) {
        var extraDeviceId =
          areaZone.sheet_extra_device_ids[
            extraIndex
          ];

        if (extraDeviceId) {
          extraDeviceIds[
            extraDeviceId
          ] = true;
        }
      }
    }

    var locationScope = {};

    for (
      var scopeIndex = 0;
      scopeIndex < locationIds.length;
      scopeIndex += 1
    ) {
      locationScope[
        locationIds[scopeIndex]
      ] = true;
    }

    var html = "";

    var delegatedPowerTargets = {};

    for (
      var delegatedIndex = 0;
      delegatedIndex < devices.length;
      delegatedIndex += 1
    ) {
      var delegatedDevice =
        devices[delegatedIndex];

      if (
        !delegatedDevice
        ||
        !delegatedDevice.power_control_device_id
      ) {
        continue;
      }

      delegatedPowerTargets[
        delegatedDevice.power_control_device_id
      ] = true;
    }

    for (
      var deviceIndex = 0;
      deviceIndex < renderDevices.length;
      deviceIndex += 1
    ) {
      var device =
        renderDevices[deviceIndex];

      if (
        !device
        ||
        (
          !locationScope[
            device.location_id
          ]
          &&
          extraDeviceIds[
            device.device_id
          ] !== true
        )
      ) {
        continue;
      }

      if (
        delegatedPowerTargets[
          device.device_id
        ]
      ) {
        continue;
      }

      var deviceState = {};
      var delegatedPowerState = {};

      for (
        var stateIndex = 0;
        stateIndex < deviceStates.length;
        stateIndex += 1
      ) {
        var state =
          deviceStates[stateIndex];

        if (
          !state ||
          state.available !== true
        ) {
          continue;
        }

        if (
          state.device_id ===
            device.device_id
        ) {
          deviceState[
            state.parameter
          ] = state.value;
        }

        if (
          device.power_control_device_id
          &&
          state.device_id ===
            device.power_control_device_id
        ) {
          delegatedPowerState[
            state.parameter
          ] = state.value;
        }
      }

      var deviceTileClass =
        "area-sheet-device area-sheet-device-tile";

      if (
        device.device_type === "light"
      ) {
        deviceTileClass +=
          " area-sheet-device-light";
      }

      /*
       * Resolve the controls that are actually visible in
       * this tile before deciding its presentation class.
       *
       * A smart light whose basic power is delegated to an
       * upstream physical switch temporarily presents only
       * that power control while the upstream power is
       * confirmed off.  In that state it should use the
       * same boolean tile presentation as other simple
       * lights, including the visible state subtitle.
       */
      var delegatedPowerControlId =
        device.power_control_device_id;

      var delegatedPowerIsOff = (
        delegatedPowerControlId
        &&
        delegatedPowerState.power === false
      );

      var controls =
        device.controls || [];

      if (delegatedPowerIsOff) {
        controls = controls.filter(
          function (control) {
            return (
              control
              &&
              control.control_id === "power"
            );
          }
        );
      }

      var tileControls = controls;

      /*
       * Presentation-only cover classification.
       *
       * Cover identity is derived from the controls already
       * used by the existing renderer.  Do not bind this
       * presentation class to a room, name or device_id.
       */
      var coverDeviceTile = tileControls.some(
        function (control) {
          return (
            control
            &&
            (
              control.control_id === "state"
              ||
              control.control_id === "position"
            )
          );
        }
      );

      if (coverDeviceTile) {
        deviceTileClass +=
          " area-sheet-device-cover";
      }

      var complexDeviceTile =
        tileControls.some(function (tileControl) {
          if (!tileControl) {
            return false;
          }

          return (
            tileControl.control_id ===
              "target_temperature"
            ||
            tileControl.control_id ===
              "position"
            ||
            tileControl.kind ===
              "multi_select"
          );
        });

      // Presentation grouping for devices with room-selection controls.
      if (tileControls.some(function (control) {
        return control && control.kind === "multi_select";
      })) {
        deviceTileClass += " area-sheet-device-room-selector";
      }

      if (complexDeviceTile) {
        deviceTileClass +=
          " area-sheet-device-control-complex";
      }

      if (
        wideDeviceIds[
          device.device_id
        ]
      ) {
        deviceTileClass +=
          " area-sheet-device-complex";
      }

      var booleanOnlyDeviceTile = (
        tileControls.length === 1
        &&
        tileControls[0]
        &&
        tileControls[0].kind === "boolean"
        &&
        device.device_type !==
          "air_purifier"
      );

      if (booleanOnlyDeviceTile) {
        deviceTileClass +=
          " area-sheet-device-boolean";

        var booleanTileValue =
          deviceState[
            tileControls[0].parameter
          ];

        /*
         * A delegated basic power control presents the
         * upstream physical power state as the visible
         * light state as well.
         *
         * Keep the tile subtitle/icon and the actual
         * delegated control on the same state source.
         */
        if (
          tileControls[0].control_id === "power"
          &&
          device.power_control_device_id
        ) {
          booleanTileValue =
            delegatedPowerState.power;
        }

        if (booleanTileValue === true) {
          deviceTileClass +=
            " area-sheet-device-boolean-on";
        } else if (
          booleanTileValue === false
        ) {
          deviceTileClass +=
            " area-sheet-device-boolean-off";
        } else {
          deviceTileClass +=
            " area-sheet-device-boolean-unknown";
        }
      }

      if (device.area_readonly === true) {
        deviceTileClass +=
          " area-sheet-device-readonly";
      }

      /*
       * Living / dining compact read-only presentation.
       *
       * Presentation only. These classes do not alter device
       * identity, state collection or control semantics.
       */
      if (
        device.device_id ===
        "living.temperature_humidity_sensor_1"
      ) {
        deviceTileClass +=
          " area-sheet-device-living-environment";
      } else if (
        device.device_id ===
        "living.entry_doorbell_1"
      ) {
        deviceTileClass +=
          " area-sheet-device-living-doorbell";
      } else if (
        device.device_id ===
        "living.entry_door_sensor_1"
      ) {
        deviceTileClass +=
          " area-sheet-device-living-door";
      }

      if (
        device.device_type ===
        "air_purifier"
      ) {
        deviceTileClass +=
          " area-sheet-device-special";
      }

      if (
        device.device_type ===
        "climate"
      ) {
        deviceTileClass +=
          " area-sheet-device-climate";
      }

      html +=
        '<div class="' +
        deviceTileClass +
        '"' +
        ' data-device-id="' +
        escapeHtml(
          device.device_id || ""
        ) +
        '">' +
        '<div class="area-sheet-device-header">' +
        (
          device.device_type === "air_purifier"
            ? (
                '<button type="button"' +
                ' class="area-sheet-device-name' +
                ' area-sheet-device-name-opener"' +
                ' data-open-special-device="' +
                escapeHtml(
                  device.device_type || ""
                ) +
                '">' +
                areaSheetDeviceIconHtml(
                  device,
                  deviceState
                ) +
                '<span class="area-sheet-device-name-text">' +
                escapeHtml(
                  device.name ||
                  device.device_id ||
                  "设备"
                ) +
                "</span>" +
                '<span class="area-sheet-device-name-arrow"' +
                ' aria-hidden="true">›</span>' +
                "</button>"
              )
            : (
                '<div class="area-sheet-device-name">' +
                areaSheetDeviceIconHtml(
                  device,
                  deviceState
                ) +
                '<span class="area-sheet-device-name-text">' +
                escapeHtml(
                  device.name ||
                  device.device_id ||
                  "设备"
                ) +
                "</span>" +
                "</div>"
              )
        ) +
        (
          device.device_type === "climate"
            ? (
                '<div class="area-sheet-climate-current">' +
                (
                  typeof deviceState.current_temperature ===
                    "number"
                  &&
                  isFinite(
                    deviceState.current_temperature
                  )
                    ? (
                        "室温 " +
                        escapeHtml(
                          String(
                            deviceState.current_temperature
                          )
                        ) +
                        " °C"
                      )
                    : "室温 —"
                ) +
                "</div>"
              )
            : ""
        ) +
        "</div>" +
        '<div class="area-sheet-device-body">';

      if (
        !device.power_control_device_id
        &&
        device.availability_reason ===
        "powered_off_by_upstream"
      ) {
        html +=
          '<div class="area-sheet-device-note">' +
          "上游电源已关闭" +
          "</div>" +
          "</div>" +
          "</div>";

        continue;
      }

      /*
       * IAM purifier summary in Area Sheet.
       *
       * The Area Sheet presents useful live readings
       * and delegates all device controls to the
       * dedicated purifier panel.
       */
      if (
        device.device_type === "air_purifier"
      ) {
        var purifierTemperature =
          deviceState.temperature;
        var purifierHumidity =
          deviceState.humidity;
        var purifierPm25 =
          deviceState.pm25;
        var purifierHcho =
          deviceState.hcho;

        function purifierSummaryValue(
          value,
          suffix
        ) {
          if (
            value === undefined
            ||
            value === null
          ) {
            return "—";
          }

          return (
            escapeHtml(String(value))
            +
            (suffix || "")
          );
        }

        html +=
          '<div class="area-sheet-purifier-summary">' +

          '<div class="area-sheet-purifier-reading">' +
          '<span class="area-sheet-purifier-label">' +
          "温度" +
          "</span>" +
          '<span class="area-sheet-purifier-value">' +
          purifierSummaryValue(
            purifierTemperature,
            " °C"
          ) +
          "</span>" +
          "</div>" +

          '<div class="area-sheet-purifier-reading">' +
          '<span class="area-sheet-purifier-label">' +
          "PM2.5" +
          "</span>" +
          '<span class="area-sheet-purifier-value">' +
          purifierSummaryValue(
            purifierPm25,
            ""
          ) +
          "</span>" +
          "</div>" +

          '<div class="area-sheet-purifier-reading">' +
          '<span class="area-sheet-purifier-label">' +
          "湿度" +
          "</span>" +
          '<span class="area-sheet-purifier-value">' +
          purifierSummaryValue(
            purifierHumidity,
            " %"
          ) +
          "</span>" +
          "</div>" +

          '<div class="area-sheet-purifier-reading">' +
          '<span class="area-sheet-purifier-label">' +
          "甲醛" +
          "</span>" +
          '<span class="area-sheet-purifier-value">' +
          purifierSummaryValue(
            purifierHcho,
            ""
          ) +
          "</span>" +
          "</div>" +

          "</div>" +

          "</div>" +
          "</div>";

        continue;
      }

      var renderedControl = false;

      for (
        var controlIndex = 0;
        controlIndex < controls.length;
        controlIndex += 1
      ) {
        var control =
          controls[controlIndex];

        if (!control) {
          continue;
        }

        if (
          control.kind === "boolean"
        ) {
          renderedControl = true;

          var currentValue =
            deviceState[
              control.parameter
            ];

          var controlDeviceAttribute = "";

          if (
            control.control_id === "power"
            &&
            delegatedPowerControlId
          ) {
            currentValue =
              delegatedPowerState[
                "power"
              ];

            controlDeviceAttribute =
              ' data-control-device-id="' +
              escapeHtml(
                delegatedPowerControlId
              ) +
              '"';
          }

          if (
            device.device_type ===
              "air_purifier"
          ) {
            var purifierControlLabel =
              deviceControlLabel(
                control.control_id
              );

            var purifierTrueLabel = (
              control.control_id === "power"
                ? "运行"
                : "开启"
            );

            var purifierFalseLabel = (
              control.control_id === "power"
                ? "停止"
                : "关闭"
            );

            html +=
              '<div class="area-sheet-control' +
              ' area-sheet-control-purifier-boolean">' +
              (
                control.control_id === "power"
                  ? ""
                  : (
                      '<div class="' +
                      'area-sheet-control-label">' +
                      escapeHtml(
                        purifierControlLabel
                      ) +
                      "</div>"
                    )
              ) +
              '<div class="device-control-buttons">' +

              '<button type="button"' +
              ' data-device-control="' +
              escapeHtml(
                control.control_id || ""
              ) +
              '"' +
              ' data-control-value="true"' +
              (
                currentValue === true
                  ? ' class="device-control-active"'
                  : ""
              ) +
              (
                currentValue === true
                  ? ' aria-pressed="true"'
                  : ' aria-pressed="false"'
              ) +
              ">" +
              escapeHtml(
                purifierTrueLabel
              ) +
              "</button>" +

              '<button type="button"' +
              ' data-device-control="' +
              escapeHtml(
                control.control_id || ""
              ) +
              '"' +
              ' data-control-value="false"' +
              (
                currentValue === false
                  ? ' class="device-control-active"'
                  : ""
              ) +
              (
                currentValue === false
                  ? ' aria-pressed="true"'
                  : ' aria-pressed="false"'
              ) +
              ">" +
              escapeHtml(
                purifierFalseLabel
              ) +
              "</button>" +

              "</div>" +
              "</div>";

            continue;
          }

          var toggleStateClass =
            "area-sheet-toggle";

          if (booleanOnlyDeviceTile) {
            toggleStateClass +=
              " area-sheet-ha-toggle";
          }

          if (
            device.device_type === "light"
            &&
            control.control_id === "power"
          ) {
            toggleStateClass +=
              " area-sheet-light-toggle";
          }

          if (currentValue === true) {
            toggleStateClass +=
              " area-sheet-toggle-on";
          } else if (
            currentValue === false
          ) {
            toggleStateClass +=
              " area-sheet-toggle-off";
          } else {
            toggleStateClass +=
              " area-sheet-toggle-unknown";
          }

          var toggleStateValue = (
            currentValue === true
              ? "true"
              : (
                  currentValue === false
                    ? "false"
                    : "unknown"
                )
          );

          html +=
            '<div class="area-sheet-control' +
            ' area-sheet-control-boolean' +
            (
              booleanOnlyDeviceTile
                ? ' area-sheet-control-ha-tile'
                : ''
            ) +
            '">' +
            '<div class="area-sheet-control-label">' +
            escapeHtml(
              deviceControlLabel(
                control.control_id
              )
            ) +
            "</div>" +
            '<div class="device-control-buttons">' +
            '<button type="button"' +
            ' class="' +
            toggleStateClass +
            '"' +
            ' data-device-control="' +
            escapeHtml(
              control.control_id || ""
            ) +
            '"' +
            ' data-control-toggle="true"' +
            ' data-current-value="' +
            toggleStateValue +
            '"' +
            controlDeviceAttribute +
            (
              currentValue === true
                ? ' aria-pressed="true"'
                : ' aria-pressed="false"'
            ) +
            (
              currentValue === true
                ? ' aria-label="关闭"'
                : (
                    currentValue === false
                      ? ' aria-label="打开"'
                      : ' aria-label="状态未知" disabled'
                  )
            ) +
            '><span class="area-sheet-toggle-knob">' +
            (
              device.device_type === "light"
              &&
              control.control_id === "power"
                ? (
                    '<span class="' +
                    'area-sheet-toggle-light-icon"' +
                    ' aria-hidden="true">' +
                    areaSheetLightStateIconSvg(
                      currentValue === true
                    ) +
                    '</span>'
                  )
                : (
                    '<span class="' +
                    'area-sheet-toggle-symbol"' +
                    ' aria-hidden="true"></span>'
                  )
            ) +
            "</span></button>" +
            "</div>" +
            "</div>";

          continue;
        }

        if (
          control.kind === "number"
        ) {
          renderedControl = true;

          var numberStateValue =
            deviceState[
              control.parameter
            ];

          var numberStateAvailable = (
            typeof numberStateValue
            === "number"
            &&
            isFinite(
              numberStateValue
            )
          );

          var numberIncrement = (
            control.step !== undefined
            && control.step !== null
              ? Number(control.step)
              : 1
          );

          var controlMinimum =
            control.min;

          var controlMaximum =
            control.max;

          if (
            control.control_id
            === "brightness"
          ) {
            numberIncrement = 5;
          } else if (
            control.control_id
            === "color_temperature"
          ) {
            numberIncrement = 100;
          } else if (
            control.control_id
            === "position"
          ) {
            numberIncrement = 10;
          }

          var numberUnit =
            deviceControlNumberUnit(
              control.control_id
            );

          var numberDisplayValue = (
            numberStateAvailable
              ? String(
                  numberStateValue
                ) + numberUnit
              : "状态未知"
          );

          var numberControlClass =
            "area-sheet-control";

          if (
            control.control_id === "position"
          ) {
            numberControlClass +=
              " area-sheet-control-cover-position";
          }

          if (
            device.device_type === "climate"
            &&
            control.control_id ===
              "target_temperature"
          ) {
            numberControlClass +=
              " area-sheet-control-climate-temperature";
          }

          html +=
            '<div class="' +
            numberControlClass +
            '">' +
            '<div class="area-sheet-control-label">' +
            escapeHtml(
              deviceControlLabel(
                control.control_id
              )
            ) +
            "</div>" +
            '<div class="device-control-buttons">' +

            '<button type="button"' +
            ' data-device-control="' +
            escapeHtml(
              control.control_id || ""
            ) +
            '"' +
            ' data-control-delta="' +
            escapeHtml(
              String(
                -numberIncrement
              )
            ) +
            '"' +
            (
              numberStateAvailable
              &&
              (
                typeof controlMinimum
                !== "number"
                ||
                numberStateValue
                > controlMinimum
              )
                ? ""
                : " disabled"
            ) +
            ">−</button>" +

            '<button type="button" disabled>' +
            escapeHtml(
              numberDisplayValue
            ) +
            "</button>" +

            '<button type="button"' +
            ' data-device-control="' +
            escapeHtml(
              control.control_id || ""
            ) +
            '"' +
            ' data-control-delta="' +
            escapeHtml(
              String(
                numberIncrement
              )
            ) +
            '"' +
            (
              numberStateAvailable
              &&
              (
                typeof controlMaximum
                !== "number"
                ||
                numberStateValue
                < controlMaximum
              )
                ? ""
                : " disabled"
            ) +
            ">+</button>" +

            "</div>" +
            "</div>";
        }

        if (
          control.kind === "select"
        ) {
          renderedControl = true;

          var selectOptions = (
            control.options || []
          );

          var selectStateValue =
            deviceState[
              control.parameter
            ];

          var selectControlClass =
            "area-sheet-control";

          if (
            control.control_id === "state"
          ) {
            selectControlClass +=
              " area-sheet-control-cover-state";
          }

          if (
            device.device_type === "climate"
          ) {
            if (
              control.control_id ===
                "operating_state"
            ) {
              selectControlClass +=
                " area-sheet-control-climate-mode";
            } else if (
              control.control_id ===
                "fan_mode"
            ) {
              selectControlClass +=
                " area-sheet-control-climate-fan";
            }
          }

          html +=
            '<div class="' +
            selectControlClass +
            '">' +
            '<div class="area-sheet-control-label">' +
            escapeHtml(
              deviceControlLabel(
                control.control_id
              )
            ) +
            "</div>" +
            '<div class="device-control-buttons">';

          for (
            var optionIndex = 0;
            optionIndex < selectOptions.length;
            optionIndex += 1
          ) {
            var optionValue =
              selectOptions[optionIndex];

            html +=
              '<button type="button"' +
              ' data-device-control="' +
              escapeHtml(
                control.control_id || ""
              ) +
              '"' +
              ' data-control-value="' +
              escapeHtml(
                String(optionValue)
              ) +
              '"' +
              (
                String(selectStateValue)
                === String(optionValue)
                  ? ' class="device-control-active"'
                  : ""
              ) +
              ">" +
              escapeHtml(
                deviceControlOptionLabel(
                  control.control_id,
                  String(optionValue)
                )
              ) +
              "</button>";
          }

          html +=
            "</div>" +
            "</div>";
        }

        if (
          control.kind === "action"
        ) {
          renderedControl = true;

          html +=
            '<div class="area-sheet-control">' +
            '<div class="area-sheet-control-label">' +
            escapeHtml(
              deviceControlLabel(
                control.control_id
              )
            ) +
            "</div>" +
            '<div class="device-control-buttons">' +
            '<button type="button"' +
            ' data-device-control="' +
            escapeHtml(
              control.control_id || ""
            ) +
            '"' +
            ' data-control-action="true"' +
            ">" +
            "开始" +
            "</button>" +
            "</div>" +
            "</div>";

          continue;
        }

        if (
          control.kind === "multi_select"
        ) {
          renderedControl = true;

          var multiSelectOptions = (
            control.options || []
          );

          html +=
            '<div class="area-sheet-control">' +
            '<div class="area-sheet-control-label">' +
            escapeHtml(
              deviceControlLabel(
                control.control_id
              )
            ) +
            "</div>" +
            '<div class="device-control-buttons">';

          for (
            var multiOptionIndex = 0;
            multiOptionIndex <
              multiSelectOptions.length;
            multiOptionIndex += 1
          ) {
            var multiOptionValue =
              multiSelectOptions[
                multiOptionIndex
              ];

            html +=
              '<button type="button"' +
              ' data-device-control="' +
              escapeHtml(
                control.control_id || ""
              ) +
              '"' +
              ' data-multi-select-option="' +
              escapeHtml(
                String(
                  multiOptionValue
                )
              ) +
              '"' +
              ">" +
              escapeHtml(
                deviceControlOptionLabel(
                  control.control_id,
                  String(
                    multiOptionValue
                  )
                )
              ) +
              "</button>";
          }

          html +=
            '<button type="button"' +
            ' data-device-control="' +
            escapeHtml(
              control.control_id || ""
            ) +
            '"' +
            ' data-multi-select-submit="true"' +
            ">" +
            "开始区域清扫" +
            "</button>" +
            "</div>" +
            "</div>";

          continue;
        }
      }

      if (
        !renderedControl &&
        controls.length > 0
      ) {
        html +=
          '<div class="area-sheet-device-note">' +
          "更多控制请进入设备详情" +
          "</div>";
      }

      /*
       * Living / dining compact read-only summaries.
       *
       * Presentation only.
       *
       * Keep the underlying Device Data and observations
       * unchanged. These three devices receive a compact
       * Area Sheet representation only.
       */
      var compactLivingReadOnlyRendered = false;

      if (
        device.device_id ===
        "living.temperature_humidity_sensor_1"
      ) {
        var livingEnvironmentParts = [];

        if (
          typeof deviceState.temperature === "number"
          &&
          isFinite(deviceState.temperature)
        ) {
          livingEnvironmentParts.push(
            "温度 " +
            formatNumericDisplay(
              deviceState.temperature
            ) +
            " °C"
          );
        }

        if (
          typeof deviceState.humidity === "number"
          &&
          isFinite(deviceState.humidity)
        ) {
          livingEnvironmentParts.push(
            "湿度 " +
            formatNumericDisplay(
              deviceState.humidity
            ) +
            " %"
          );
        }

        if (
          typeof deviceState.battery_level === "number"
          &&
          isFinite(deviceState.battery_level)
        ) {
          html +=
            '<div class="' +
            'area-sheet-living-battery"' +
            ' aria-label="电量 ' +
            escapeHtml(
              formatNumericDisplay(
                deviceState.battery_level
              )
            ) +
            '%">' +
            '<span class="' +
            'area-sheet-living-battery-icon"' +
            ' aria-hidden="true"></span>' +
            '<span>' +
            escapeHtml(
              formatNumericDisplay(
                deviceState.battery_level
              )
            ) +
            '%</span>' +
            '</div>';
        }

        if (livingEnvironmentParts.length > 0) {
          html +=
            '<div class="' +
            'area-sheet-living-environment-values">' +
            escapeHtml(
              livingEnvironmentParts.join("　")
            ) +
            '</div>';
        }

        compactLivingReadOnlyRendered = true;
      } else if (
        device.device_id ===
        "living.entry_doorbell_1"
      ) {
        if (
          typeof deviceState.battery_level === "number"
          &&
          isFinite(deviceState.battery_level)
        ) {
          html +=
            '<div class="' +
            'area-sheet-living-inline-state">' +
            '<span class="' +
            'area-sheet-living-battery-icon"' +
            ' aria-hidden="true"></span>' +
            '<span>' +
            escapeHtml(
              formatNumericDisplay(
                deviceState.battery_level
              )
            ) +
            '%</span>' +
            '</div>';
        }

        compactLivingReadOnlyRendered = true;
      } else if (
        device.device_id ===
        "living.entry_door_sensor_1"
      ) {
        if (
          typeof deviceState.open === "boolean"
        ) {
          html +=
            '<div class="' +
            'area-sheet-living-inline-state">' +
            (
              deviceState.open
                ? "已打开"
                : "已关闭"
            ) +
            '</div>';
        }

        compactLivingReadOnlyRendered = true;
      }

      var readOnlyStates = [
        {
          parameter: "electric_power",
          label: "当前功率",
          unit: " W"
        },
        {
          parameter: "energy",
          label: "累计用电",
          unit: " kWh"
        },
        {
          parameter: "voltage",
          label: "电压",
          unit: " V"
        },
        {
          parameter: "open",
          label: "门状态",
          unit: ""
        },
        {
          parameter: "temperature",
          label: "温度",
          unit: " °C"
        },
        {
          parameter: "humidity",
          label: "湿度",
          unit: " %"
        },
        {
          parameter: "battery_level",
          label: "电量",
          unit: " %"
        },
        {
          parameter: "operating_state",
          label: "工作状态",
          unit: ""
        },
        {
          parameter: "cleaning",
          label: "清扫",
          unit: ""
        },
        {
          parameter: "water_shortage",
          label: "供水",
          unit: ""
        },
        {
          parameter: "clean_water_box_problem",
          label: "清水箱",
          unit: ""
        },
        {
          parameter: "dirty_water_box_problem",
          label: "脏水箱",
          unit: ""
        },
        {
          parameter: "vacuum_error",
          label: "机器人",
          unit: ""
        },
        {
          parameter: "dock_error",
          label: "基站",
          unit: ""
        }
      ];

      for (
        var readOnlyIndex = 0;
        !compactLivingReadOnlyRendered
        &&
        readOnlyIndex < readOnlyStates.length;
        readOnlyIndex += 1
      ) {
        var readOnlyState =
          readOnlyStates[readOnlyIndex];

        if (
          readOnlyState.parameter === "operating_state"
          &&
          controls.some(function (control) {
            return (
              control.control_id ===
              "target_temperature"
            );
          })
        ) {
          continue;
        }

        if (
          !Object.prototype.hasOwnProperty.call(
            deviceState,
            readOnlyState.parameter
          )
        ) {
          continue;
        }

        var readOnlyValue =
          deviceState[
            readOnlyState.parameter
          ];

        if (
          readOnlyValue === null
          ||
          readOnlyValue === undefined
        ) {
          continue;
        }

        var readOnlyDisplayValue = (
          (
            typeof readOnlyValue === "number"
              ? formatNumericDisplay(
                  readOnlyValue
                )
              : String(readOnlyValue)
          )
          + readOnlyState.unit
        );

        if (
          readOnlyState.parameter === "open"
          &&
          typeof readOnlyValue === "boolean"
        ) {
          readOnlyDisplayValue = (
            readOnlyValue
              ? "已打开"
              : "已关闭"
          );
        }

        if (
          readOnlyState.parameter === "charging"
          &&
          typeof readOnlyValue === "boolean"
        ) {
          readOnlyDisplayValue = (
            readOnlyValue
              ? "充电中"
              : "未充电"
          );
        }

        if (
          readOnlyState.parameter === "cleaning"
          &&
          typeof readOnlyValue === "boolean"
        ) {
          readOnlyDisplayValue = (
            readOnlyValue
              ? "正在清扫"
              : "未运行"
          );
        }

        if (
          readOnlyState.parameter === "water_shortage"
          &&
          typeof readOnlyValue === "boolean"
        ) {
          readOnlyDisplayValue = (
            readOnlyValue
              ? "缺水"
              : "正常"
          );
        }

        if (
          (
            readOnlyState.parameter
            === "clean_water_box_problem"
            ||
            readOnlyState.parameter
            === "dirty_water_box_problem"
          )
          &&
          typeof readOnlyValue === "boolean"
        ) {
          readOnlyDisplayValue = (
            readOnlyValue
              ? "异常"
              : "正常"
          );
        }

        if (
          readOnlyState.parameter === "vacuum_error"
          &&
          String(readOnlyValue).toLowerCase()
          === "none"
        ) {
          readOnlyDisplayValue = "正常";
        }

        if (
          readOnlyState.parameter === "dock_error"
          &&
          String(readOnlyValue).toLowerCase()
          === "ok"
        ) {
          readOnlyDisplayValue = "正常";
        }

        if (
          readOnlyState.parameter
          === "operating_state"
        ) {
          var operatingStateLabels = {
            charging: "充电中",
            charging_complete: "充电完成",
            docked: "已停靠",
            cleaning: "正在清扫",
            segment_cleaning: "分区清扫中",
            zoned_cleaning: "区域清扫中",
            spot_cleaning: "局部清扫中",
            returning: "回充中",
            returning_home: "回充中",
            docking: "回充中",
            paused: "已暂停",
            idle: "空闲",
            washing_the_mop: "清洗拖布",
            washing_the_mop_2: "清洗拖布",
            going_to_wash_the_mop: "前往清洗拖布",
            emptying_the_bin: "集尘中"
          };

          var normalizedOperatingState =
            String(
              readOnlyValue
            ).toLowerCase();

          if (
            Object.prototype.hasOwnProperty.call(
              operatingStateLabels,
              normalizedOperatingState
            )
          ) {
            readOnlyDisplayValue =
              operatingStateLabels[
                normalizedOperatingState
              ];
          }
        }

        html +=
          '<div class="area-sheet-control area-sheet-status-reading">' +
          '<div class="area-sheet-control-label">' +
          escapeHtml(
            readOnlyState.label
          ) +
          "</div>" +
          '<div class="area-sheet-readonly-value">' +
          escapeHtml(
            readOnlyDisplayValue
          ) +
          "</div>" +
          "</div>";
      }

      html +=
        "</div>" +
        "</div>";
    }

    if (!html) {
      html =
        '<div class="area-sheet-empty">' +
        "当前没有可控设备" +
        "</div>";
    }

    title.innerHTML = escapeHtml(
      areaSheetTitleLabel(
        locationId,
        locations
      )
    );

    content.innerHTML = html;

    collapseAreaSheetPowerGroups(
      content,
      devices,
      deviceStates
    );

    /*
     * Living / dining compact status stack.
     *
     * Presentation only.
     *
     * Keep the environment sensor, entry doorbell and entry
     * door sensor as independent device tiles, but compose
     * them into one visual column in the combined
     * living/dining Area Sheet.
     *
     * Device identity, state collection and control semantics
     * remain unchanged.
     */
    if (locationId === "home_living_dining") {
      var livingStatusStackIds = [
        "living.temperature_humidity_sensor_1",
        "living.entry_doorbell_1",
        "living.entry_door_sensor_1"
      ];

      var livingStatusTiles = [];

      for (
        var livingStatusIndex = 0;
        livingStatusIndex <
          livingStatusStackIds.length;
        livingStatusIndex += 1
      ) {
        var livingStatusTile =
          content.querySelector(
            '[data-device-id="' +
            livingStatusStackIds[
              livingStatusIndex
            ] +
            '"]'
          );

        if (livingStatusTile) {
          livingStatusTiles.push(
            livingStatusTile
          );
        }
      }

      if (livingStatusTiles.length > 0) {
        var livingStatusStack =
          document.createElement("div");

        livingStatusStack.className =
          "area-sheet-living-status-stack";

        content.insertBefore(
          livingStatusStack,
          livingStatusTiles[0]
        );

        for (
          var livingStatusTileIndex = 0;
          livingStatusTileIndex <
            livingStatusTiles.length;
          livingStatusTileIndex += 1
        ) {
          livingStatusStack.appendChild(
            livingStatusTiles[
              livingStatusTileIndex
            ]
          );
        }
      }
    }

    /*
     * Area Sheet Adaptive Layout V2
     *
     * Classify from the FINAL visible tiles after delegated
     * power groups have been collapsed.
     *
     * Device count controls density; intrinsically complex
     * controls such as climate, curtain position and robot
     * multi-select receive additional horizontal room.
     *
     * Presentation only.
     */
    var visibleDeviceCount = (
      content.getElementsByClassName(
        "area-sheet-device"
      ).length
    );

    var complexDeviceCount = (
      content.getElementsByClassName(
        "area-sheet-device-control-complex"
      ).length
    );

    var areaSheetLayoutClass =
      "area-sheet-layout-medium";

    if (
      visibleDeviceCount <= 2
      &&
      complexDeviceCount === 0
    ) {
      areaSheetLayoutClass =
        "area-sheet-layout-compact";
    } else if (
      visibleDeviceCount >= 7
    ) {
      areaSheetLayoutClass =
        "area-sheet-layout-dense";
    } else if (
      complexDeviceCount > 0
    ) {
      areaSheetLayoutClass =
        "area-sheet-layout-complex";
    }

    if (
      visibleDeviceCount <= 3
      && content.getElementsByClassName(
        "area-sheet-device-room-selector"
      ).length === 1
    ) {
      areaSheetLayoutClass += " area-sheet-layout-room-selector";
    }

    activeAreaLocationId = locationId;

    sheet.className =
      "area-sheet area-sheet-open " +
      areaSheetLayoutClass +
      (
        locationId === "home_living_dining"
          ? " area-sheet-living-dining"
          : ""
      );

    sheet.setAttribute(
      "aria-hidden",
      "false"
    );
  }


  function bindAreaOverview() {
    var container = document.getElementById(
      "area-overview"
    );
    var sheet = document.getElementById(
      "area-sheet"
    );

    if (!container) {
      return;
    }

    container.onclick = function (event) {
      event = event || window.event;

      var target = (
        event.target ||
        event.srcElement
      );

      while (
        target &&
        target !== container &&
        !target.getAttribute(
          "data-location-id"
        )
      ) {
        target = target.parentNode;
      }

      if (
        !target ||
        target === container
      ) {
        return;
      }

      var locationId =
        target.getAttribute(
          "data-location-id"
        );

      if (!locationId) {
        return;
      }

      renderAreaSheet(
        locationId,
        latestDashboardZones,
        latestDashboardDevices,
        latestDashboardDeviceStates,
        latestDashboardLocations
      );
    };

    if (!sheet) {
      return;
    }


    var areaSheetToggleDrag = null;
    var suppressAreaSheetToggleClick = false;

    function areaSheetToggleTarget(node) {
      var current = node;

      while (
        current &&
        current !== sheet
      ) {
        if (
          current.tagName === "BUTTON"
          &&
          current.getAttribute(
            "data-control-toggle"
          ) !== null
        ) {
          return current;
        }

        current = current.parentNode;
      }

      return null;
    }


    function areaSheetToggleKnob(target) {
      if (!target) {
        return null;
      }

      var children =
        target.getElementsByTagName(
          "span"
        );

      for (
        var childIndex = 0;
        childIndex < children.length;
        childIndex += 1
      ) {
        var child = children[childIndex];

        if (
          (
            " " +
            (child.className || "") +
            " "
          ).indexOf(
            " area-sheet-toggle-knob "
          ) >= 0
        ) {
          return child;
        }
      }

      return null;
    }


    function resetAreaSheetToggleDragVisual(
      target,
      knob
    ) {
      if (target) {
        target.style.removeProperty(
          "--area-sheet-toggle-drag-x"
        );
      }

      if (knob) {
        knob.style.left = "";
        knob.style.transition = "";
      }
    }


    sheet.onpointerdown = function (event) {
      event = event || window.event;

      if (
        deviceControlRequestPending
        ||
        (
          event.button !== undefined
          &&
          event.button !== 0
        )
      ) {
        return;
      }

      var target =
        areaSheetToggleTarget(
          event.target ||
          event.srcElement
        );

      if (!target || target.disabled) {
        return;
      }

      var rawCurrent =
        target.getAttribute(
          "data-current-value"
        );

      if (
        rawCurrent !== "true"
        &&
        rawCurrent !== "false"
      ) {
        return;
      }

      var knob =
        areaSheetToggleKnob(
          target
        );

      if (!knob) {
        return;
      }

      var rect =
        target.getBoundingClientRect();

      var knobRect =
        knob.getBoundingClientRect();

      var minLeft = 4;
      var maxLeft = Math.max(
        minLeft,
        rect.width
          - knobRect.width
          - 4
      );

      areaSheetToggleDrag = {
        target: target,
        knob: knob,
        pointerId: event.pointerId,
        startX: event.clientX,
        lastX: event.clientX,
        currentOn:
          rawCurrent === "true",
        minLeft: minLeft,
        maxLeft: maxLeft,
        dragged: false
      };

      knob.style.transition = "none";

      if (
        target.setPointerCapture
        &&
        event.pointerId !== undefined
      ) {
        try {
          target.setPointerCapture(
            event.pointerId
          );
        } catch (error) {
          // Ignore unsupported capture errors.
        }
      }
    };


    sheet.onpointermove = function (event) {
      event = event || window.event;

      if (!areaSheetToggleDrag) {
        return;
      }

      if (
        event.pointerId !== undefined
        &&
        areaSheetToggleDrag.pointerId
          !== undefined
        &&
        event.pointerId
          !== areaSheetToggleDrag.pointerId
      ) {
        return;
      }

      var drag = areaSheetToggleDrag;

      drag.lastX = event.clientX;

      var deltaX =
        drag.lastX - drag.startX;

      if (
        Math.abs(deltaX) >= 5
      ) {
        drag.dragged = true;
      }

      if (!drag.dragged) {
        return;
      }

      if (event.preventDefault) {
        event.preventDefault();
      }

      var startLeft = (
        drag.currentOn
          ? drag.maxLeft
          : drag.minLeft
      );

      var nextLeft = Math.max(
        drag.minLeft,
        Math.min(
          drag.maxLeft,
          startLeft + deltaX
        )
      );

      drag.knob.style.left =
        String(nextLeft) + "px";
    };


    function finishAreaSheetToggleDrag(
      event,
      cancelled
    ) {
      if (!areaSheetToggleDrag) {
        return;
      }

      var drag = areaSheetToggleDrag;

      if (
        event
        &&
        event.pointerId !== undefined
        &&
        drag.pointerId !== undefined
        &&
        event.pointerId !== drag.pointerId
      ) {
        return;
      }

      areaSheetToggleDrag = null;

      if (
        drag.target.releasePointerCapture
        &&
        drag.pointerId !== undefined
      ) {
        try {
          drag.target.releasePointerCapture(
            drag.pointerId
          );
        } catch (error) {
          // Ignore unsupported capture errors.
        }
      }

      if (
        cancelled
        ||
        !drag.dragged
      ) {
        resetAreaSheetToggleDragVisual(
          drag.target,
          drag.knob
        );
        return;
      }

      suppressAreaSheetToggleClick = true;

      window.setTimeout(
        function () {
          suppressAreaSheetToggleClick = false;
        },
        0
      );

      var finalX = (
        event
        &&
        event.clientX !== undefined
          ? event.clientX
          : drag.lastX
      );

      var rect =
        drag.target.getBoundingClientRect();

      var desiredOn =
        finalX >= (
          rect.left +
          rect.width / 2
        );

      resetAreaSheetToggleDragVisual(
        drag.target,
        drag.knob
      );

      if (
        desiredOn === drag.currentOn
      ) {
        return;
      }

      var controlId =
        drag.target.getAttribute(
          "data-device-control"
        );

      if (!controlId) {
        return;
      }

      var panel = drag.target;

      while (
        panel &&
        panel !== sheet &&
        !panel.getAttribute(
          "data-device-id"
        )
      ) {
        panel = panel.parentNode;
      }

      if (
        !panel ||
        panel === sheet
      ) {
        return;
      }

      var panelDeviceId =
        panel.getAttribute(
          "data-device-id"
        );

      var controlDeviceId =
        drag.target.getAttribute(
          "data-control-device-id"
        );

      var deviceId = (
        controlDeviceId
        || panelDeviceId
      );

      if (
        !deviceId
        ||
        deviceControlRequestPending
      ) {
        return;
      }

      sendDeviceControl(
        deviceId,
        controlId,
        desiredOn,
        drag.target
      );
    }


    sheet.onpointerup = function (event) {
      finishAreaSheetToggleDrag(
        event || window.event,
        false
      );
    };


    sheet.onpointercancel = function (event) {
      finishAreaSheetToggleDrag(
        event || window.event,
        true
      );
    };


    /*
     * Legacy iPad Safari fallback.
     *
     * Older Safari versions do not implement Pointer Events.
     * Reuse the same drag state and control dispatch through
     * touchstart / touchmove / touchend instead of creating a
     * second control path.
     */
    if (!window.PointerEvent) {
      sheet.ontouchstart = function (event) {
        event = event || window.event;

        if (
          !event.touches
          ||
          event.touches.length !== 1
        ) {
          return;
        }

        var touch = event.touches[0];

        sheet.onpointerdown({
          target:
            event.target ||
            event.srcElement,
          srcElement:
            event.srcElement,
          clientX: touch.clientX
        });
      };


      sheet.ontouchmove = function (event) {
        event = event || window.event;

        if (
          !areaSheetToggleDrag
          ||
          !event.touches
          ||
          event.touches.length !== 1
        ) {
          return;
        }

        var touch = event.touches[0];

        sheet.onpointermove({
          clientX: touch.clientX,
          preventDefault: function () {
            if (event.preventDefault) {
              event.preventDefault();
            }

            event.returnValue = false;
          }
        });
      };


      sheet.ontouchend = function (event) {
        event = event || window.event;

        if (!areaSheetToggleDrag) {
          return;
        }

        var touch = (
          event.changedTouches
          &&
          event.changedTouches.length
            ? event.changedTouches[0]
            : null
        );

        finishAreaSheetToggleDrag(
          {
            clientX: (
              touch
                ? touch.clientX
                : areaSheetToggleDrag.lastX
            )
          },
          false
        );

        if (event.preventDefault) {
          event.preventDefault();
        }

        event.returnValue = false;
      };


      sheet.ontouchcancel = function (event) {
        finishAreaSheetToggleDrag(
          null,
          true
        );
      };
    }


    sheet.onclick = function (event) {
      event = event || window.event;

      if (suppressAreaSheetToggleClick) {
        suppressAreaSheetToggleClick = false;
        return;
      }

      var target = (
        event.target ||
        event.srcElement
      );

      if (!target) {
        return;
      }

      if (
        target.getAttribute(
          "data-area-sheet-close"
        ) !== null
      ) {
        closeAreaSheet();
        return;
      }

      if (
        target.tagName !== "BUTTON"
      ) {
        return;
      }

      var controlId =
        target.getAttribute(
          "data-device-control"
        );
      var rawValue =
        target.getAttribute(
          "data-control-value"
        );

      var rawToggle =
        target.getAttribute(
          "data-control-toggle"
        );

      var rawCurrent =
        target.getAttribute(
          "data-current-value"
        );

      var rawDelta =
        target.getAttribute(
          "data-control-delta"
        );

      var rawAction =
        target.getAttribute(
          "data-control-action"
        );

      var multiSelectOption =
        target.getAttribute(
          "data-multi-select-option"
        );

      var multiSelectSubmit =
        target.getAttribute(
          "data-multi-select-submit"
        );

      if (
        !controlId ||
        deviceControlRequestPending
      ) {
        return;
      }

      if (
        multiSelectOption !== null
      ) {
        var activeClass =
          "device-control-active";

        var className =
          target.className || "";

        if (
          (
            " " + className + " "
          ).indexOf(
            " " + activeClass + " "
          ) >= 0
        ) {
          target.className = (
            " " + className + " "
          ).replace(
            " " + activeClass + " ",
            " "
          ).replace(
            /^\s+|\s+$/g,
            ""
          );
        } else {
          target.className = (
            className
              ? className + " "
              : ""
          ) + activeClass;
        }

        return;
      }

      if (
        rawValue === null
        && rawToggle === null
        && rawDelta === null
        && rawAction === null
        && multiSelectSubmit === null
      ) {
        return;
      }

      var panel = target;

      while (
        panel &&
        panel !== sheet &&
        !panel.getAttribute(
          "data-device-id"
        )
      ) {
        panel = panel.parentNode;
      }

      if (
        !panel ||
        panel === sheet
      ) {
        return;
      }

      var panelDeviceId =
        panel.getAttribute(
          "data-device-id"
        );

      var controlDeviceId =
        target.getAttribute(
          "data-control-device-id"
        );

      var deviceId = (
        controlDeviceId
        || panelDeviceId
      );

      if (!deviceId) {
        return;
      }

      var value;

      if (rawAction !== null) {
        value = null;
      } else if (
        rawToggle !== null
      ) {
        if (rawCurrent === "true") {
          value = false;
        } else if (
          rawCurrent === "false"
        ) {
          value = true;
        } else {
          setDeviceControlStatus(
            "设备状态未知，暂时无法切换",
            true
          );
          return;
        }
      } else if (
        multiSelectSubmit !== null
      ) {
        var selectedValues = [];

        var panelButtons =
          panel.getElementsByTagName(
            "button"
          );

        for (
          var selectedIndex = 0;
          selectedIndex <
            panelButtons.length;
          selectedIndex += 1
        ) {
          var selectedButton =
            panelButtons[
              selectedIndex
            ];

          if (
            selectedButton.getAttribute(
              "data-device-control"
            ) !== controlId
          ) {
            continue;
          }

          var selectedOption =
            selectedButton.getAttribute(
              "data-multi-select-option"
            );

          if (
            selectedOption === null
          ) {
            continue;
          }

          var selectedClassName =
            selectedButton.className || "";

          if (
            (
              " " +
              selectedClassName +
              " "
            ).indexOf(
              " device-control-active "
            ) < 0
          ) {
            continue;
          }

          selectedValues.push(
            selectedOption
          );
        }

        if (
          selectedValues.length === 0
        ) {
          setDeviceControlStatus(
            "请至少选择一个清扫区域",
            true
          );

          return;
        }

        value = selectedValues;
      } else if (rawDelta !== null) {
        var matchingDevice = null;

        for (
          var deviceLookupIndex = 0;
          deviceLookupIndex
          < latestDashboardDevices.length;
          deviceLookupIndex += 1
        ) {
          if (
            latestDashboardDevices[
              deviceLookupIndex
            ].device_id
            === deviceId
          ) {
            matchingDevice =
              latestDashboardDevices[
                deviceLookupIndex
              ];
            break;
          }
        }

        if (!matchingDevice) {
          return;
        }

        var matchingControl = null;
        var matchingControls =
          matchingDevice.controls || [];

        for (
          var controlLookupIndex = 0;
          controlLookupIndex
          < matchingControls.length;
          controlLookupIndex += 1
        ) {
          if (
            matchingControls[
              controlLookupIndex
            ].control_id
            === controlId
          ) {
            matchingControl =
              matchingControls[
                controlLookupIndex
              ];
            break;
          }
        }

        if (!matchingControl) {
          return;
        }

        var currentNumber = null;

        for (
          var stateLookupIndex = 0;
          stateLookupIndex
          < latestDashboardDeviceStates.length;
          stateLookupIndex += 1
        ) {
          var currentState =
            latestDashboardDeviceStates[
              stateLookupIndex
            ];

          if (
            currentState.device_id
            === deviceId
            &&
            currentState.parameter
            === matchingControl.parameter
            &&
            currentState.available
            === true
          ) {
            currentNumber = parseFloat(
              currentState.value
            );
            break;
          }
        }

        var numberDelta = parseFloat(
          rawDelta
        );

        if (
          currentNumber === null
          ||
          Number.isNaN(currentNumber)
          ||
          Number.isNaN(numberDelta)
        ) {
          return;
        }

        value =
          currentNumber
          + numberDelta;

        var controlMinimum =
          matchingControl.min;

        var controlMaximum =
          matchingControl.max;

        if (
          typeof controlMinimum
          === "number"
        ) {
          value = Math.max(
            controlMinimum,
            value
          );
        }

        if (
          typeof controlMaximum
          === "number"
        ) {
          value = Math.min(
            controlMaximum,
            value
          );
        }
      } else {
        value = rawValue;

        if (rawValue === "true") {
          value = true;
        } else if (
          rawValue === "false"
        ) {
          value = false;
        }
      }

      sendDeviceControl(
        deviceId,
        controlId,
        value,
        target
      );
    };
  }


  function formatNumericDisplay(
    value
  ) {
    var numericValue = Number(value);

    if (!isFinite(numericValue)) {
      return String(value);
    }

    var roundedValue =
      Math.round(
        numericValue * 100
      ) / 100;

    return String(roundedValue);
  }


  function formatTemperatureDisplay(
    value
  ) {
    var numericValue = Number(value);

    if (!isFinite(numericValue)) {
      return null;
    }

    var roundedValue =
      Math.round(
        numericValue * 10
      ) / 10;

    return (
      String(roundedValue)
      + " °C"
    );
  }


  function areaTemperatureDisplay(
    locationId,
    deviceStates
  ) {
    var sources = {
      open_public_area: {
        device_id: "living.temperature_humidity_sensor_1",
        parameter: "temperature"
      },
      master_bedroom: {
        device_id: "master_bedroom.temperature_humidity_sensor_1",
        parameter: "temperature"
      },
      study: {
        device_id: "study.air_conditioner_1",
        parameter: "current_temperature"
      },
      princess_room: {
        device_id: "princess_room.air_conditioner_1",
        parameter: "current_temperature"
      }
    };

    var source = sources[locationId];

    if (!source) {
      return null;
    }

    deviceStates = deviceStates || [];

    for (
      var index = 0;
      index < deviceStates.length;
      index += 1
    ) {
      var state = deviceStates[index];

      if (
        !state
        ||
        state.device_id !== source.device_id
        ||
        state.parameter !== source.parameter
        ||
        state.available !== true
      ) {
        continue;
      }

      if (
        state.value === null
        ||
        state.value === undefined
      ) {
        return null;
      }

      return formatTemperatureDisplay(
        state.value
      );
    }

    return null;
  }


  function renderAreaOverview(
    cards,
    locations,
    deviceStates,
    zones
  ) {
    var container = document.getElementById(
      "area-overview"
    );

    if (!container) {
      return;
    }

    cards = cards || [];
    locations = locations || [];
    deviceStates = deviceStates || [];
    zones = zones || [];

    var lightingDeviceIdsByRoom = {
      corridor: {
        "corridor.light_1": true
      },
      living: {
        "living.main_light_power_1": true,
        "living.light_strip_1": true,
        "living.downlight_1": true
      },
      dining: {
        "dining.light_power_1": true,
        "dining.atmosphere_light_1": true
      },
      kitchen: {
        "kitchen.light_1": true
      },
      master_bedroom: {
        "master_bedroom.main_light_power_1": true,
        "master_bedroom.light_strip_1": true,
        "master_bedroom.downlight_1": true
      },
      study: {
        "study.ceiling_light_1": true
      },
      princess_room: {
        "princess_room.ceiling_light_power_1": true,
        "princess_room.spotlight_1": true,
        "princess_room.light_strip_1": true
      },
      master_bath: {
        "master_bath.makeup_light_1": true,
        "master_bath.bathing_light_1": true
      },
      guest_bath: {
        "guest_bath.makeup_light_1": true,
        "guest_bath.bathing_light_1": true
      }
    };

    var homeZones = [];

    for (
      var zoneIndex = 0;
      zoneIndex < zones.length;
      zoneIndex += 1
    ) {
      var zone = zones[zoneIndex];

      if (
        !zone ||
        zone.show_on_home !== true ||
        !zone.zone_id
      ) {
        continue;
      }

      var roomIds = zone.room_ids || [];

      if (!roomIds.length) {
        continue;
      }

      homeZones.push(zone);
    }

    homeZones.sort(
      function (left, right) {
        var leftOrder =
          typeof left.location_order === "number"
            ? left.location_order
            : 9999;

        var rightOrder =
          typeof right.location_order === "number"
            ? right.location_order
            : 9999;

        if (leftOrder !== rightOrder) {
          return leftOrder - rightOrder;
        }

        return String(
          left.zone_id
        ).localeCompare(
          String(
            right.zone_id
          )
        );
      }
    );

    var areaHtml = "";

    for (
      var homeZoneIndex = 0;
      homeZoneIndex < homeZones.length;
      homeZoneIndex += 1
    ) {
      var homeZone =
        homeZones[homeZoneIndex];

      areaHtml +=
        '<button type="button"' +
        ' class="area-card"' +
        ' data-location-id="' +
        escapeHtml(
          homeZone.zone_id
        ) +
        '">' +
        '<span class="area-card-name">' +
        escapeHtml(
          homeZone.location_label ||
          homeZone.zone_id
        ) +
        "</span>" +
        '<span class="area-card-state">' +
        "" +
        "</span>" +
        "</button>";
    }

    container.innerHTML = areaHtml;

    var semanticByLocation = {};

    for (
      var cardIndex = 0;
      cardIndex < cards.length;
      cardIndex += 1
    ) {
      var card = cards[cardIndex];

      if (
        !card ||
        !card.location_id ||
        !card.value
      ) {
        continue;
      }

      if (
        card.target !== "occupancy" &&
        card.target !== "lighting" &&
        card.target !== "comfort"
      ) {
        continue;
      }

      if (
        !semanticByLocation[
          card.location_id
        ]
      ) {
        semanticByLocation[
          card.location_id
        ] = {};
      }

      semanticByLocation[
        card.location_id
      ][card.target] = card;
    }

    var areaCards =
      container.querySelectorAll(
        "[data-location-id]"
      );

    for (
      var areaIndex = 0;
      areaIndex < areaCards.length;
      areaIndex += 1
    ) {
      var areaCard = areaCards[areaIndex];
      var locationId =
        areaCard.getAttribute(
          "data-location-id"
        );
      var stateNode =
        areaCard.querySelector(
          ".area-card-state"
        );

      if (!stateNode) {
        continue;
      }

      var presentationZone = null;

      for (
        var zoneLookupIndex = 0;
        zoneLookupIndex < homeZones.length;
        zoneLookupIndex += 1
      ) {
        if (
          homeZones[
            zoneLookupIndex
          ].zone_id === locationId
        ) {
          presentationZone =
            homeZones[
              zoneLookupIndex
            ];
          break;
        }
      }

      var summaryLocationId = (
        presentationZone &&
        presentationZone.summary_location_id
          ? presentationZone.summary_location_id
          : locationId
      );

      var semantic =
        semanticByLocation[
          summaryLocationId
        ] || {};

      var presentationRoomIds = (
        presentationZone &&
        presentationZone.room_ids &&
        presentationZone.room_ids.length > 0
          ? presentationZone.room_ids
          : [summaryLocationId]
      );

      var lightingDeviceIds = {};

      for (
        var lightingRoomIndex = 0;
        lightingRoomIndex
        < presentationRoomIds.length;
        lightingRoomIndex += 1
      ) {
        var lightingRoomId =
          presentationRoomIds[
            lightingRoomIndex
          ];

        var roomLightingDeviceIds =
          lightingDeviceIdsByRoom[
            lightingRoomId
          ] || {};

        for (
          var lightingDeviceId
          in roomLightingDeviceIds
        ) {
          if (
            Object.prototype.hasOwnProperty.call(
              roomLightingDeviceIds,
              lightingDeviceId
            )
          ) {
            lightingDeviceIds[
              lightingDeviceId
            ] = true;
          }
        }
      }

      var lightsOn = false;

      for (
        var lightingStateIndex = 0;
        lightingStateIndex
        < deviceStates.length;
        lightingStateIndex += 1
      ) {
        var state =
          deviceStates[
            lightingStateIndex
          ];

        if (
          state &&
          state.available === true &&
          state.parameter === "power" &&
          state.value === true &&
          lightingDeviceIds[
            state.device_id
          ] === true
        ) {
          lightsOn = true;
          break;
        }
      }

      if (lightsOn) {
        areaCard.className +=
          " area-card-lights-on";
      }

      var parts = [];

      var temperatureDisplay =
        areaTemperatureDisplay(
          summaryLocationId,
          deviceStates
        );

      if (temperatureDisplay) {
        parts.push(temperatureDisplay);
      }

      var occupancy =
        semantic["occupancy"];

      var isOccupied = (
        occupancy &&
        occupancy.value &&
        occupancy.value.state ===
          "occupied"
      );

      if (isOccupied) {
        parts.push("有人");
      }

      var comfort =
        semantic["comfort"];

      if (
        comfort &&
        comfort.value &&
        comfort.value.level &&
        comfort.value.level !==
          "comfortable"
      ) {
        parts.push(
          "舒适度需留意"
        );
      }

      var lighting =
        semantic["lighting"];

      var isDim = (
        lighting &&
        lighting.value &&
        lighting.value.state ===
          "dim"
      );

      if (isOccupied && isDim) {
        parts.push(
          "光线偏暗"
        );
      }

      if (isOccupied) {
        areaCard.className +=
          " area-card-occupied";
      }

      if (isOccupied && isDim) {
        areaCard.className +=
          " area-card-dim";
      }

      if (parts.length > 0) {
        var primaryParts = [];
        var secondaryParts = [];

        if (temperatureDisplay) {
          primaryParts.push(
            temperatureDisplay
          );
        }

        for (
          var partIndex = 0;
          partIndex < parts.length;
          partIndex += 1
        ) {
          if (
            parts[partIndex]
            === temperatureDisplay
          ) {
            continue;
          }

          secondaryParts.push(
            parts[partIndex]
          );
        }

        var stateHtml = "";

        if (primaryParts.length > 0) {
          stateHtml +=
            '<span class="area-card-state-primary">' +
            escapeHtml(
              primaryParts.join(" · ")
            ) +
            "</span>";
        }

        if (secondaryParts.length > 0) {
          stateHtml +=
            '<span class="area-card-state-secondary">';

          for (
            var secondaryIndex = 0;
            secondaryIndex <
              secondaryParts.length;
            secondaryIndex += 1
          ) {
            stateHtml +=
              '<span class="area-card-state-item">' +
              escapeHtml(
                secondaryParts[
                  secondaryIndex
                ]
              ) +
              "</span>";
          }

          stateHtml += "</span>";
        }

        stateNode.innerHTML =
          stateHtml;

        continue;
      }

      stateNode.innerHTML = "";
    }
  }


  function updateSemanticDashboard() {
    var request = new XMLHttpRequest();

    request.onreadystatechange = function () {
      if (
        request.readyState !== 4 ||
        request.status !== 200
      ) {
        return;
      }

      var payload;

      try {
        payload = JSON.parse(
          request.responseText
        );
      } catch (error) {
        return;
      }

      var cards = sortSemanticCards(
        payload.cards || []
      );
      var locations = payload.locations || [];
      var observations =
        payload.observations || [];
      var deviceStates =
        payload.device_states || [];
      var devices =
        payload.devices || [];
      var zones =
        payload.zones || [];

      latestDashboardZones = zones;
      latestDashboardDevices = devices;
      latestDashboardDeviceStates =
        deviceStates;
      latestDashboardLocations = locations;

      if (activeAreaLocationId) {
        renderAreaSheet(
          activeAreaLocationId,
          zones,
          devices,
          deviceStates,
          locations
        );
      }

      var seenSemanticNodeIds = {};

      renderFamilySummary(
        cards,
        zones,
        deviceStates,
        devices
      );

      renderAreaOverview(
        cards,
        locations,
        deviceStates,
        zones
      );

      bindSpecialDevicePanels(
        devices
      );

      renderGenericObservations(
        observations
      );

      renderGenericDeviceControls(
        devices,
        deviceStates
      );

      renderXingooDeviceControlState(
        observations
      );

      for (var i = 0; i < cards.length; i += 1) {
        if (cards[i].target === "weather_status") {
          var weather = cards[i].value || {};

          var weatherIcon =
            document.getElementById("weather-icon");

          if (weatherIcon) {
            weatherIcon.className =
              "weather-icon " +
              weatherIconClass(
                weather.condition
              );
          }

          document.getElementById("condition").innerHTML =
            formatWeatherCondition(
              weather.condition
            );

          document.getElementById("temperature").innerHTML =
            weather.temperature != null
              ? weather.temperature + " °C"
              : "--";

          document.getElementById(
            "apparent-temperature"
          ).innerHTML =
            weather.apparent_temperature != null
              ? "体感 " +
                weather.apparent_temperature.toFixed(1) +
                " " +
                (
                  weather.apparent_temperature_unit === "degC"
                    ? "°C"
                    : (
                        weather.apparent_temperature_unit
                        || "°C"
                      )
                )
              : "--";

          document.getElementById("humidity").innerHTML =
            weather.humidity != null
              ? "湿度 " + weather.humidity + "%"
              : "--";

          document.getElementById("wind").innerHTML =
            weather.wind_speed != null
              ? "风速 " + weather.wind_speed + " " +
                (
                  weather.wind_speed_unit
                  || "km/h"
                )
              : "--";


          var observed = formatObservedAt(
            cards[i].updated_at
          );

          setUpdateStatus(
            "fresh",
            observed
              ? "更新于 " + observed
              : "数据已更新"
          );

        } else if (
          cards[i].target === "occupancy"
        ) {
          var occupancyNodeId = semanticStatusNodeId(
            "semantic-occupancy-status",
            cards[i].location_id
          );

          seenSemanticNodeIds[
            occupancyNodeId
          ] = true;

          renderOccupancyCard(cards[i]);
        } else if (
          cards[i].target === "lighting"
        ) {
          var lightingNodeId = semanticStatusNodeId(
            "semantic-lighting-status",
            cards[i].location_id
          );

          seenSemanticNodeIds[
            lightingNodeId
          ] = true;

          renderLightingCard(cards[i]);
        } else if (
          cards[i].target === "comfort"
        ) {
          var comfortNodeId = semanticStatusNodeId(
            "semantic-comfort-status",
            cards[i].location_id
          );

          seenSemanticNodeIds[
            comfortNodeId
          ] = true;

          renderComfortCard(cards[i]);
        } else if (
          cards[i].target === "umbrella_advice"
        ) {
          var umbrellaNodeId = semanticStatusNodeId(
            "semantic-umbrella-advice",
            cards[i].location_id
          );

          seenSemanticNodeIds[
            umbrellaNodeId
          ] = true;

          renderUmbrellaAdviceCard(
            cards[i]
          );
        } else if (
          cards[i].target === "clothing_advice"
        ) {
          var clothingNodeId = semanticStatusNodeId(
            "semantic-clothing-advice",
            cards[i].location_id
          );

          seenSemanticNodeIds[
            clothingNodeId
          ] = true;

          renderClothingAdviceCard(
            cards[i]
          );
        }
      }

      for (
        var locationIndex = 0;
        locationIndex < locations.length;
        locationIndex += 1
      ) {
        renderRoomAvailability(
          locations[locationIndex],
          seenSemanticNodeIds
        );
      }

      removeStaleSemanticStatusItems(
        seenSemanticNodeIds
      );

      if (
        locations.length === 0 &&
        Object.keys(seenSemanticNodeIds).length === 0
      ) {
        renderSemanticEmptyState();
      } else {
        removeSemanticEmptyState();
      }
    };

    request.open(
      "GET",
      "/api/dashboard",
      true
    );
    request.send();
  }

  function scheduleSemanticDashboardRefresh() {
    if (semanticDashboardRefreshTimer !== null) {
      clearTimeout(
        semanticDashboardRefreshTimer
      );
    }

    var interval = (
      dashboardStateEventsConnected
        ? SEMANTIC_CONNECTED_INTERVAL_MS
        : SEMANTIC_FALLBACK_INTERVAL_MS
    );

    semanticDashboardRefreshTimer = setTimeout(
      function () {
        updateSemanticDashboard();
        scheduleSemanticDashboardRefresh();
      },
      interval
    );
  }

  function subscribeDashboardStateEvents() {
    if (!window.EventSource) {
      dashboardStateEventsConnected = false;
      scheduleSemanticDashboardRefresh();
      return;
    }

    var eventSource = new EventSource(
      "/api/dashboard/events"
    );

    eventSource.onopen = function () {
      dashboardStateEventsConnected = true;
      scheduleSemanticDashboardRefresh();
    };

    eventSource.onerror = function () {
      dashboardStateEventsConnected = false;
      scheduleSemanticDashboardRefresh();
    };

    eventSource.addEventListener(
      "dashboard-state-changed",
      function () {
        updateSemanticDashboard();
      }
    );
  }

  function subscribeHomeStatusEvents() {
    if (!window.EventSource) {
      return;
    }

    var eventSource = new EventSource(
      "/api/home/events"
    );

    eventSource.addEventListener("home-status-changed",
      function () {
        updateHomeStatusCard();
      }
    );
  }


  var deviceControlRequestPending = false;


  function setDeviceControlStatus(
    message,
    isError
  ) {
    var status = document.getElementById(
      "xingoo-air-purifier-control-status"
    );

    if (!status) {
      return;
    }

    status.innerHTML = message || "";

    status.className =
      "device-control-status" +
      (
        isError
          ? " device-control-error"
          : ""
      );
  }


  function setDeviceControlButtonsDisabled(
    disabled
  ) {
    var panel = document.getElementById(
      "xingoo-air-purifier-controls"
    );

    if (!panel) {
      return;
    }

    var buttons = panel.getElementsByTagName(
      "button"
    );

    for (
      var i = 0;
      i < buttons.length;
      i += 1
    ) {
      buttons[i].disabled = disabled;
    }
  }


  function sendHouseholdAction(
    actionId,
    sourceButton
  ) {
    var request = new XMLHttpRequest();

    if (sourceButton) {
      sourceButton.disabled = true;
    }

    request.onreadystatechange = function () {
      if (request.readyState !== 4) {
        return;
      }

      if (sourceButton) {
        sourceButton.disabled = false;
      }

      if (
        request.status < 200 ||
        request.status >= 300
      ) {
        setDeviceControlStatus(
          "家庭操作失败",
          true
        );
        return;
      }

      var result = null;

      try {
        result = JSON.parse(
          request.responseText
        );
      } catch (error) {
      }

      if (
        result &&
        result.status ===
          "partial_failure"
      ) {
        setDeviceControlStatus(
          "部分设备未响应",
          true
        );
      } else {
        setDeviceControlStatus(
          "已执行",
          false
        );
      }

      updateSemanticDashboard();
    };

    request.open(
      "POST",
      "/api/household/actions",
      true
    );

    request.setRequestHeader(
      "Content-Type",
      "application/json"
    );

    request.send(
      JSON.stringify(
        {
          action_id: actionId
        }
      )
    );
  }


  function bindHouseholdActions() {
    var container = document.getElementById(
      "household-actions"
    );

    if (!container) {
      return;
    }

    container.onclick = function (event) {
      event = event || window.event;

      var target = (
        event.target ||
        event.srcElement
      );

      if (
        !target ||
        target.tagName !== "BUTTON"
      ) {
        return;
      }

      var actionId =
        target.getAttribute(
          "data-household-action"
        );

      var supportedActions = {
        all_lights_off: true,
        night: true,
        away: true
      };

      if (!supportedActions[actionId]) {
        return;
      }

      sendHouseholdAction(
        actionId,
        target
      );
    };
  }


  function sendDeviceControl(
    deviceId,
    controlId,
    value,
    sourceButton
  ) {
    var request = new XMLHttpRequest();

    var payload = {
      device_id: deviceId,
      control_id: controlId,
      value: value
    };

    deviceControlRequestPending = true;

    if (sourceButton) {
      sourceButton.disabled = true;
    }

    setDeviceControlStatus(
      "正在发送并确认状态...",
      false
    );

    request.onreadystatechange = function () {
      if (request.readyState !== 4) {
        return;
      }

      deviceControlRequestPending = false;

      if (sourceButton) {
        sourceButton.disabled = false;
      }

      if (
        request.status < 200 ||
        request.status >= 300
      ) {
        var errorMessage = "控制失败";

        try {
          var errorPayload = JSON.parse(
            request.responseText
          );

          if (errorPayload.error) {
            errorMessage =
              errorPayload.error;
          }
        } catch (error) {
        }

        setDeviceControlStatus(
          errorMessage,
          true
        );

        return;
      }

      setDeviceControlStatus(
        "命令已发送",
        false
      );

      updateSemanticDashboard();
    };

    request.open(
      "POST",
      "/api/device/actions",
      true
    );

    request.setRequestHeader(
      "Content-Type",
      "application/json"
    );

    request.send(
      JSON.stringify(
        payload
      )
    );
  }


  var specialDeviceOverlay = null;


  function ensureSpecialDeviceOverlay() {
    if (specialDeviceOverlay) {
      return specialDeviceOverlay;
    }

    var overlay =
      document.createElement("div");

    overlay.className =
      "special-device-overlay";
    overlay.setAttribute(
      "aria-hidden",
      "true"
    );

    var sheet =
      document.createElement("div");

    sheet.className =
      "special-device-sheet";

    var closeButton =
      document.createElement("button");

    closeButton.type = "button";
    closeButton.className =
      "special-device-close";
    closeButton.innerHTML = "×";
    closeButton.setAttribute(
      "aria-label",
      "关闭"
    );

    var body =
      document.createElement("div");

    body.className =
      "special-device-body";

    closeButton.onclick = function () {
      overlay.className =
        "special-device-overlay";
      overlay.setAttribute(
        "aria-hidden",
        "true"
      );
    };

    overlay.onclick = function (event) {
      if (event.target === overlay) {
        closeButton.onclick();
      }
    };

    sheet.appendChild(closeButton);
    sheet.appendChild(body);
    overlay.appendChild(sheet);
    document.body.appendChild(overlay);

    specialDeviceOverlay = {
      root: overlay,
      body: body
    };

    return specialDeviceOverlay;
  }


  function openSpecialDevicePanel(
    deviceType
  ) {
    if (!deviceType) {
      return;
    }

    var panels =
      document.getElementsByClassName(
        "device-control-section"
      );

    var panel = null;

    for (
      var i = 0;
      i < panels.length;
      i += 1
    ) {
      if (
        panels[i].getAttribute(
          "data-device-type"
        ) === deviceType
      ) {
        panel = panels[i];
        break;
      }
    }

    if (!panel) {
      return;
    }

    var overlay =
      ensureSpecialDeviceOverlay();

    overlay.body.appendChild(panel);

    overlay.root.className =
      "special-device-overlay special-device-overlay-open";

    overlay.root.setAttribute(
      "aria-hidden",
      "false"
    );
  }


  function bindSpecialDevicePanelOpeners() {
    document.addEventListener(
      "click",
      function (event) {
        var target =
          event.target ||
          event.srcElement;

        while (
          target &&
          target !== document &&
          !target.getAttribute(
            "data-open-special-device"
          )
        ) {
          target = target.parentNode;
        }

        if (
          !target ||
          target === document
        ) {
          return;
        }

        var deviceType =
          target.getAttribute(
            "data-open-special-device"
          );

        if (!deviceType) {
          return;
        }

        event.preventDefault();
        openSpecialDevicePanel(deviceType);
      }
    );
  }

  function bindDeviceControls() {
    var panel = document.getElementById(
      "xingoo-air-purifier-controls"
    );

    if (!panel) {
      return;
    }

    panel.onclick = function (event) {
      event = event || window.event;

      var target = (
        event.target ||
        event.srcElement
      );

      if (
        !target ||
        target.tagName !== "BUTTON"
      ) {
        return;
      }

      var controlId = target.getAttribute(
        "data-device-control"
      );

      var rawValue = target.getAttribute(
        "data-control-value"
      );

      var deviceId = panel.getAttribute(
        "data-device-id"
      );

      if (
        !deviceId ||
        !controlId ||
        rawValue === null
      ) {
        return;
      }

      if (deviceControlRequestPending) {
        return;
      }

      var value = rawValue;

      if (rawValue === "true") {
        value = true;
      } else if (
        rawValue === "false"
      ) {
        value = false;
      }

      sendDeviceControl(
        deviceId,
        controlId,
        value,
        target
      );
    };
  }

  bindCalendarOverlay();
  bindTodos();
  bindAreaOverview();
  bindHouseholdActions();
  bindSpecialDevicePanelOpeners();
  bindDeviceControls();
  updateDashboard();
  refreshTodayCalendar();
  updatePhotoCard();
  updateTodoCard();
  updateHomeStatusCard();
  updateSemanticDashboard();
  scheduleSemanticDashboardRefresh();
  subscribeDashboardStateEvents();
  subscribeHomeStatusEvents();

  // Calendar recovery must not depend on the household snapshot succeeding.
  setInterval(refreshTodayCalendar, 15000);
  setInterval(updateDashboard, 30000);
  setInterval(updatePhotoCard, 60000);
  setInterval(updateTodoCard, 30000);
  setInterval(updateHomeStatusCard, 5000);
  setInterval(showNextPhoto, 15000);
})();
