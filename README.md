## === scan result for last PR/commit status === 
<br/><br/>
###### SCA scan by Synopsys Black Duck
|OSS component | Version | Status | noVuln Version| Latest Version |
| --- | --- | --- | --- | --- |
|adm-zip|0.4.4| in VIOLATION|0.4.9|0.4.18|
|chownr|1.0.1| in VIOLATION|1.1.0|2.0.0|
|chownr|1.1.1| in VIOLATION|v1.1.2|2.0.0|
|cryptiles|2.0.5| in VIOLATION|v3.2.0|v5.1.0|
|cryptiles|0.2.2| in VIOLATION|v3.2.0|v5.1.0|
|dot-prop|4.2.0| in VIOLATION|v5.1.1|v5.2.0|
|fstream|1.0.10| in VIOLATION|1.0.12|1.0.12|
|Growl|1.9.2| in VIOLATION|1.10.2|1.10.2|
|Handlebars.js|4.0.5| in VIOLATION|4.0.11-1|5.0.0-alpha.1.ff.0|
|is-my-json-valid|2.19.0| in VIOLATION|v2.20.4|2.20.5|
|is-my-json-valid|2.15.0| in VIOLATION|v2.20.4|2.20.5|
|isaacs's npm|3.10.10| in VIOLATION|3.13.18|v7.0.0-beta.2|
|js-bson|1.0.9| in VIOLATION|1.1.4|4.0.4|
|JS-YAML. Native JS port of PyYAML.|3.5.5| in VIOLATION|3.6.2|3.14.0|
|JS-YAML. Native JS port of PyYAML.|3.6.1| in VIOLATION|3.6.2|3.14.0|
|Lo-Dash|2.4.2| in VIOLATION|4.16.4.1|4.16.4.1|
|Lo-Dash|4.13.1| in VIOLATION|4.16.4.1|4.16.4.1|
|Lo-Dash|4.17.11| in VIOLATION|4.17.19|4.17.19|
|mime|1.2.11| in VIOLATION|v1.3.1|2.4.6|
|minimatch|0.3.0| in VIOLATION|1.0.0.0|3.0.4|
|minimist|0.0.10| in VIOLATION|0.3.0|1.2.5|
|minimist|1.2.0| in VIOLATION|1.2.2|1.2.5|
|minimist|0.0.8| in VIOLATION|0.3.0|1.2.5|
|mixin-deep|1.3.1| in VIOLATION|1.3.2|1.3.2|
|Node-cli|1.0.1| in VIOLATION|No Solution Found|No Latest version Found|
|set-value|0.4.3| in VIOLATION|2.0.1|3.0.2|
|set-value|2.0.0| in VIOLATION|2.0.1|3.0.2|
|stringstream|0.0.5| in VIOLATION|0.0.6|1.0.0|
|tar|2.2.1| in VIOLATION|v2.2.2|v6.0.2|
###### SAST scan by Synopsys Coverity
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>path</th>
      <th>checker</th>
      <th>severity</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>test/security/profile-test.js</td>
      <td>PATH_MANIPULATION</td>
      <td>audit</td>
    </tr>
    <tr>
      <th>1</th>
      <td>app/assets/vendor/bootstrap/bootstrap.js</td>
      <td>DOM_XSS</td>
      <td>audit</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Gruntfile.js</td>
      <td>OS_CMD_INJECTION</td>
      <td>high</td>
    </tr>
    <tr>
      <th>3</th>
      <td>test/security/profile-test.js</td>
      <td>PATH_MANIPULATION</td>
      <td>audit</td>
    </tr>
    <tr>
      <th>4</th>
      <td>app/data/user-dao.js</td>
      <td>INSECURE_RANDOM</td>
      <td>low</td>
    </tr>
    <tr>
      <th>5</th>
      <td>app/routes/session.js</td>
      <td>INSECURE_RANDOM</td>
      <td>low</td>
    </tr>
    <tr>
      <th>6</th>
      <td>Gruntfile.js</td>
      <td>OS_CMD_INJECTION</td>
      <td>audit</td>
    </tr>
    <tr>
      <th>7</th>
      <td>app/assets/vendor/bootstrap/bootstrap.js</td>
      <td>SCRIPT_CODE_INJECTION</td>
      <td>audit</td>
    </tr>
    <tr>
      <th>8</th>
      <td>app/assets/vendor/bootstrap/bootstrap.js</td>
      <td>DOM_XSS</td>
      <td>audit</td>
    </tr>
    <tr>
      <th>9</th>
      <td>app/assets/vendor/bootstrap/bootstrap.js</td>
      <td>SCRIPT_CODE_INJECTION</td>
      <td>audit</td>
    </tr>
    <tr>
      <th>10</th>
      <td>server.js</td>
      <td>EXPRESS_X_POWERED_BY_ENABLED</td>
      <td>low</td>
    </tr>
    <tr>
      <th>11</th>
      <td>test/security/profile-test.js</td>
      <td>PATH_MANIPULATION</td>
      <td>audit</td>
    </tr>
    <tr>
      <th>12</th>
      <td>test/security/profile-test.js</td>
      <td>PATH_MANIPULATION</td>
      <td>audit</td>
    </tr>
    <tr>
      <th>13</th>
      <td>test/security/profile-test.js</td>
      <td>PATH_MANIPULATION</td>
      <td>audit</td>
    </tr>
    <tr>
      <th>14</th>
      <td>app/views/login.html</td>
      <td>DEADCODE</td>
      <td>medium</td>
    </tr>
    <tr>
      <th>15</th>
      <td>config/env/all.js</td>
      <td>HARDCODED_CREDENTIALS</td>
      <td>medium</td>
    </tr>
    <tr>
      <th>16</th>
      <td>artifacts/db-reset.js</td>
      <td>INSECURE_RANDOM</td>
      <td>low</td>
    </tr>
  </tbody>
</table><br/>::: warning
*This is a personal hobbby project only.*
*Not associated or supported by Synopsys SIG.*
:::
