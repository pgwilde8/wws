Updated the music button link and routes to match the file structure:
Updated:
Dashboard button link - Changed from /admin/music to /admin/personal/music
Main music route - Changed from /admin/music to /admin/personal/music and updated template path to admin/personal/music/music-main.html
Other music routes - Updated to use /admin/personal/music/ prefix:
/admin/personal/music/true-solfeggio → admin/personal/music/True-Solfeggio.html
/admin/personal/music/relaxing → admin/personal/music/relaxing.html
Routes are now organized under /admin/personal:
/admin/personal - Personal dashboard
/admin/personal/music - Music library main page
/admin/personal/music/true-solfeggio - True Solfeggio folder
/admin/personal/music/relaxing - Relaxing music folder
The music button on the personal dashboard now links to /admin/personal/music, which serves the music-main.html template from the correct location.

login:https://webwisesolutions.dev/admin/personal/login
    "/admin/personal/music/soc",
https://webwisesolutions.dev/admin/file-upload

        <!-- Album 4 -->
        <div class="border-b border-gray-200 pb-4 last:border-b-0">
          <div class="flex flex-wrap items-baseline gap-3">
            <span class="font-semibold text-lg text-gray-900">Title4:</span>
            <a href="#" target="_blank" class="text-blue-600 hover:text-blue-800 hover:underline">song1</a>
            <a href="#" target="_blank" class="text-blue-600 hover:text-blue-800 hover:underline">song2</a>
            <a href="#" target="_blank" class="text-blue-600 hover:text-blue-800 hover:underline">song3</a>
          </div>
        </div>    
