from __future__ import annotations


DASHBOARD_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>SmartScreenOS</title>
  <meta
    name="viewport"
    content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"
  >
  <meta
    name="apple-mobile-web-app-capable"
    content="yes"
  >
  <meta
    name="apple-mobile-web-app-status-bar-style"
    content="black-translucent"
  >
  <meta
    name="apple-mobile-web-app-title"
    content="SmartScreenOS"
  >
  <link rel="stylesheet" href="/static/dashboard.css?v=79">
</head>
<body>
  <div class="dashboard">
    <div class="primary-panel">
      <div class="clock-panel">
        <div id="time">--:--</div>
        <div id="date">----</div>
      </div>

      <div class="weather-panel">
        <div
          id="weather-icon"
          class="weather-icon weather-icon-cloudy"
          aria-hidden="true"
        >
          <span class="sun-disc"></span>
          <i class="sun-ray sun-ray-0"></i>
          <i class="sun-ray sun-ray-1"></i>
          <i class="sun-ray sun-ray-2"></i>
          <i class="sun-ray sun-ray-3"></i>
          <i class="sun-ray sun-ray-4"></i>
          <i class="sun-ray sun-ray-5"></i>
          <i class="sun-ray sun-ray-6"></i>
          <i class="sun-ray sun-ray-7"></i>
        </div>
        <div id="condition">--</div>
        <div id="temperature">--</div>

        <div class="weather-details">
          <div id="apparent-temperature">--</div>
          <div id="humidity">--</div>
          <div id="wind">--</div>
        </div>
      </div>
    </div>

    <div class="content-panel">
      <div id="dashboard-content">
        <div class="dashboard-cards">
          <div class="dashboard-card" id="photo-card">
            <div class="dashboard-card-title">照片</div>
            <div class="dashboard-card-body">
              <img id="photo-image" alt="SmartScreenOS 照片">
              <div id="photo-empty">正在加载照片...</div>
            </div>
          </div>

          <div class="home-summary">
            <div class="home-overview-row">
              <div
                class="dashboard-card home-overview-card"
                id="today-card"
                role="button"
                tabindex="0"
                aria-haspopup="dialog"
                aria-controls="calendar-overlay"
              >
                <div
                  class="dashboard-card-body"
                  id="today-summary"
                >
                  正在加载日期...
                </div>
              </div>

              <div
                class="dashboard-card home-overview-card"
                id="todo-card"
                role="button"
                tabindex="0"
                aria-haspopup="dialog"
                aria-controls="todo-overlay"
              >
                <div class="dashboard-card-title">
                  待办事项
                </div>
                <div
                  class="dashboard-card-body"
                  id="todo-summary"
                >
                  正在加载待办...
                </div>
              </div>

              <div
                class="dashboard-card home-overview-card"
                id="reminder-card"
              >
                <div class="dashboard-card-title">
                  提醒
                </div>
                <div
                  class="dashboard-card-body"
                  id="reminder-list"
                >
                  暂无需要处理的事项
                </div>
              </div>
            </div>

            <div
              class="area-overview"
              id="area-overview"
            ></div>

          </div>

          <div class="dashboard-card" id="home-status-card">
            <div class="dashboard-card-title">家庭状态</div>
            <div class="dashboard-card-body">
              <div id="home-status-list">正在加载家庭状态...</div>
              <div id="semantic-status-list"></div>

              <div class="observation-status-section">
                <div class="observation-status-title">
                  传感器数据
                </div>
                <div id="observation-status-list"></div>
              </div>

              <div
                class="device-control-section"
                id="xingoo-air-purifier-controls"
                data-device-type="air_purifier"
              >
                <div class="device-control-title">
                  IAM消毒空气净化器
                </div>

                <div class="purifier-detail-readings">
                  <div class="purifier-detail-reading">
                    <div
                      class="purifier-detail-reading-value"
                      data-purifier-reading="temperature"
                    >—</div>
                    <div class="purifier-detail-reading-label">
                      温度
                    </div>
                  </div>

                  <div class="purifier-detail-reading">
                    <div
                      class="purifier-detail-reading-value"
                      data-purifier-reading="humidity"
                    >—</div>
                    <div class="purifier-detail-reading-label">
                      湿度
                    </div>
                  </div>

                  <div class="purifier-detail-reading">
                    <div
                      class="purifier-detail-reading-value"
                      data-purifier-reading="pm25"
                    >—</div>
                    <div class="purifier-detail-reading-label">
                      PM2.5
                    </div>
                  </div>

                  <div class="purifier-detail-reading">
                    <div
                      class="purifier-detail-reading-value"
                      data-purifier-reading="hcho"
                    >—</div>
                    <div class="purifier-detail-reading-label">
                      甲醛
                    </div>
                  </div>
                </div>

                <div class="device-control-group purifier-control-power">
                  <div class="device-control-label">电源</div>
                  <div class="device-control-buttons">
                    <button
                      type="button"
                      data-device-control="power"
                      data-control-value="true"
                    >开机</button>
                    <button
                      type="button"
                      data-device-control="power"
                      data-control-value="false"
                    >关机</button>
                  </div>
                </div>

                <div class="device-control-group purifier-control-mode">
                  <div class="device-control-label">模式</div>
                  <div class="device-control-buttons">
                    <button
                      type="button"
                      data-device-control="mode"
                      data-control-value="smart"
                    >智能</button>
                    <button
                      type="button"
                      data-device-control="mode"
                      data-control-value="sleep"
                    >睡眠</button>
                  </div>
                </div>

                <div class="device-control-group purifier-control-wind">
                  <div class="device-control-label">风速</div>
                  <div class="device-control-buttons">
                    <button
                      type="button"
                      data-device-control="wind_speed"
                      data-control-value="1"
                    >1</button>
                    <button
                      type="button"
                      data-device-control="wind_speed"
                      data-control-value="2"
                    >2</button>
                    <button
                      type="button"
                      data-device-control="wind_speed"
                      data-control-value="3"
                    >3</button>
                    <button
                      type="button"
                      data-device-control="wind_speed"
                      data-control-value="4"
                    >4</button>
                    <button
                      type="button"
                      data-device-control="wind_speed"
                      data-control-value="5"
                    >5</button>
                  </div>
                </div>

                <div class="device-control-group purifier-control-secondary purifier-control-ions">
                  <div class="device-control-label">负离子</div>
                  <div class="device-control-buttons">
                    <button
                      type="button"
                      data-device-control="ions"
                      data-control-value="true"
                    >开</button>
                    <button
                      type="button"
                      data-device-control="ions"
                      data-control-value="false"
                    >关</button>
                  </div>
                </div>

                <div class="device-control-group purifier-control-secondary purifier-control-disinfection">
                  <div class="device-control-label">消毒</div>
                  <div class="device-control-buttons">
                    <button
                      type="button"
                      data-device-control="disinfection"
                      data-control-value="true"
                    >开</button>
                    <button
                      type="button"
                      data-device-control="disinfection"
                      data-control-value="false"
                    >关</button>
                  </div>
                </div>

                <div class="device-control-group purifier-control-secondary purifier-control-screen">
                  <div class="device-control-label">屏幕</div>
                  <div class="device-control-buttons">
                    <button
                      type="button"
                      data-device-control="screen_on"
                      data-control-value="true"
                    >亮屏</button>
                    <button
                      type="button"
                      data-device-control="screen_on"
                      data-control-value="false"
                    >息屏</button>
                  </div>
                </div>

                <div class="device-control-group purifier-control-secondary purifier-control-lock">
                  <div class="device-control-label">童锁</div>
                  <div class="device-control-buttons">
                    <button
                      type="button"
                      data-device-control="child_lock"
                      data-control-value="true"
                    >锁定</button>
                    <button
                      type="button"
                      data-device-control="child_lock"
                      data-control-value="false"
                    >解锁</button>
                  </div>
                </div>

                <div
                  class="device-control-status"
                  id="xingoo-air-purifier-control-status"
                ></div>
              </div>

              <div
                id="generic-device-controls"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
              class="household-actions"
              id="household-actions"
            >
              <button
                type="button"
                data-household-action="away"
              >离家</button>
              <button
                type="button"
                data-household-action="night"
              >夜间</button>
              <button
                type="button"
                data-household-action="all_lights_off"
              >全部关灯</button>
              <button
                type="button"
                data-household-action="more"
              >更多</button>

              <a
                class="music-shortcut"
                id="music-shortcut"
                href="https://music.apple.com/"
                aria-label="打开音乐"
              >
                <span
                  class="music-shortcut-icon"
                  aria-hidden="true"
                >♪</span>
                <span>音乐</span>
              </a>

              <span
                id="update-status"
                class="update-status update-status-pending"
                title="等待数据"
                aria-label="数据状态"
              ></span>
            </div>
  </div>

  <div
    class="calendar-overlay"
    id="calendar-overlay"
    aria-hidden="true"
  >
    <button
      type="button"
      class="calendar-overlay-backdrop"
      data-calendar-close
      aria-label="关闭日历"
    ></button>

    <section
      class="calendar-overlay-panel"
      role="dialog"
      aria-modal="true"
      aria-labelledby="calendar-overlay-title"
    >
      <div class="calendar-overlay-header">
        <div>
          <div class="calendar-overlay-eyebrow">
            家庭日历
          </div>
          <h2 id="calendar-overlay-title">
            未来 10 天
          </h2>
        </div>

        <button
          class="calendar-overlay-close"
          type="button"
          data-calendar-close
          aria-label="关闭日历"
        >
          ×
        </button>
      </div>

      <div class="calendar-overlay-content">
        <div id="calendar-overlay-list">
          正在加载日历...
        </div>
      </div>
    </section>
  </div>

  <div
    class="todo-overlay"
    id="todo-overlay"
    aria-hidden="true"
  >
    <button
      type="button"
      class="todo-overlay-backdrop"
      data-todo-close
      aria-label="关闭待办事项"
    ></button>

    <section
      class="todo-overlay-panel"
      role="dialog"
      aria-modal="true"
      aria-labelledby="todo-overlay-title"
    >
      <div class="todo-overlay-header">
        <div>
          <div class="todo-overlay-eyebrow">
            家庭事项
          </div>
          <h2 id="todo-overlay-title">
            待办事项
          </h2>
        </div>

        <button
          class="todo-overlay-close"
          type="button"
          data-todo-close
          aria-label="关闭待办事项"
        >
          ×
        </button>
      </div>

      <div class="todo-overlay-content">
        <form
          id="todo-add-form"
          class="todo-add-form"
        >
          <label
            class="todo-input-label"
            for="todo-new-title"
          >
            新增待办
          </label>
          <input
            id="todo-new-title"
            type="text"
            maxlength="200"
            placeholder="添加一件事…"
            autocomplete="off"
          >
          <button
            id="todo-add-button"
            type="submit"
          >
            添加
          </button>
        </form>

        <div
          id="todo-feedback"
          role="status"
          aria-live="polite"
        ></div>

        <div class="todo-overlay-toolbar">
          <button
            id="todo-show-completed"
            type="button"
            aria-pressed="false"
          >
            查看已完成
          </button>
        </div>

        <div id="todo-list">
          正在加载待办...
        </div>
      </div>
    </section>
  </div>

  <div
    class="area-sheet"
    id="area-sheet"
    aria-hidden="true"
  >
    <button
      type="button"
      class="area-sheet-backdrop"
      data-area-sheet-close
      aria-label="关闭区域详情"
    ></button>

    <section
      class="area-sheet-panel"
      role="dialog"
      aria-modal="true"
      aria-labelledby="area-sheet-title"
    >
      <div class="area-sheet-header">
        <div>
          <div class="area-sheet-eyebrow">
            区域
          </div>
          <h2 id="area-sheet-title">
            区域详情
          </h2>
        </div>

        <button
          type="button"
          class="area-sheet-close"
          data-area-sheet-close
          aria-label="关闭"
        >
          ×
        </button>
      </div>

      <div
        class="area-sheet-content"
        id="area-sheet-content"
      >
        暂无设备
      </div>
    </section>
  </div>

  <script src="/static/dashboard.js?v=60"></script>
</body>
</html>
""".encode("utf-8")
