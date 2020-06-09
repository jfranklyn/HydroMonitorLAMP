<!--
 John Franklyn 06/03/2020 
Read sensor data from closet sensors. Added logic to read
 from right or left closet
-->
<?php
    include_once('pihydropdata-database.php');
    if ($_GET["readingsCount"]){
      $data = $_GET["readingsCount"];
      $data = trim($data);
      $data = stripslashes($data);
      $data = htmlspecialchars($data);
      $readings_count = $_GET["readingsCount"];
    }
    // default readings count set to 20
    else {
      $readings_count = 20;
    }
//  get the readings for each sensor and one location    
    $location = 'right closet';
    $sensor = 'temperature';

    $last_reading = getLastReadings($sensor,$location);
    $last_reading_temp = round($last_reading["dblvalueraw"], 2);
    echo "last reading temp = $last_reading_temp <br>";

    $sensor = 'humidity';
    $last_reading = getLastReadings($sensor,$location);
    $last_reading_humi = round($last_reading["dblvalueraw"], 2);
    echo "last reading humidity = $last_reading_humi<br>";
    
    $sensor = 'pressure';
    $last_reading = getLastReadings($sensor,$location);
    $last_reading_press = $last_reading["dblvalueraw"];

    $sensor = 'ph';
    $last_reading = getLastReadings($sensor,$location);
    $last_reading_ph = $last_reading["dblvalueraw"];

    $sensor = 'rpo';
    $last_reading = getLastReadings($sensor,$location);
    $last_reading_rpo = $last_reading["dblvalueraw"];

    $sensor = 'ec';
    $last_reading = getLastReadings($sensor,$location);
    $last_reading_ec = $last_reading["dblvalueraw"];    

    $last_reading_time = getLastReadings("reading_time","","",$location);

    // Uncomment to set timezone to - 1 hour (you can change 1 to any number)
    //$last_reading_time = date("Y-m-d H:i:s", strtotime("$last_reading_time - 1 hours"));
    // Uncomment to set timezone to + 7 hours (you can change 7 to any number)
    $last_reading_time = date("m-d-Y H:i:s", strtotime("$last_reading_time + 7 hours"));

//  calculate min, max, average values based on rowcount
    $sensor = 'temperature';
    $min_temp = minReading($readings_count, 'dblvalueraw', $sensor, $location);
    $max_temp = maxReading($readings_count, 'dblvalueraw', $sensor, $location);
    $avg_temp = avgReading($readings_count, 'dblvalueraw', $sensor, $location);

    $sensor = 'humidity';
    $min_humi = minReading($readings_count, 'dblvalueraw', $sensor, $location);
    $max_humi = maxReading($readings_count, 'dblvalueraw', $sensor, $location);
    $avg_humi = avgReading($readings_count, 'dblvalueraw', $sensor, $location);

    $sensor = 'pressure';
    $min_press = minReading($readings_count, 'dblvalueraw', $sensor, $location);
    $max_press = maxReading($readings_count, 'dblvalueraw',$sensor, $location);
    $avg_press = avgReading($readings_count, 'dblvalueraw', $sensor,  $location);

    $sensor = 'ph';
    $min_ph = minReading($readings_count, 'dblvalueraw', $sensor, $location);
    $max_ph = maxReading($readings_count, 'dblvalueraw', $sensor, $location);
    $avg_ph = avgReading($readings_count, 'dblvalueraw', $sensor, $location);

    $sensor = 'rpo';
    $min_rpo = minReading($readings_count, 'dblvalueraw', $sensor, $location);
    $max_rpo = maxReading($readings_count, 'dblvalueraw', $sensor, $location);
    $avg_rpo = avgReading($readings_count, 'dblvalueraw', $sensor, $location);

    $sensor = 'ec';
    $min_ec = minReading($readings_count, 'dblvalueraw', $sensor, $location);
    $max_ec = maxReading($readings_count, 'dblvalueraw', $sensor, $location);
    $avg_ec = avgReading($readings_count, 'dblvalueraw', $sensor, $location);

?>

<!DOCTYPE html>
<html>
    <head>
   <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
   <script type="text/javascript">
      google.charts.load('current', {'packages':['gauge']});
      google.charts.setOnLoadCallback(drawChart);

      function drawChart() {
        var data = google.visualization.arrayToDataTable([
          ['Label', 'Value'],
          ['Temperature - C', $last_reading_temp],
          ['Humidity - RH', $last_reading_humi],
          ['Pressure - Pa', $last_reading_press],
          ['Ph - #', $last_reading_ph],
          ['ORP - mV', $last_reading_rpo],
          ['EC - R', $last_reading_ec]
        ]);

        var options = {
          width: 500, height: 200,
          redFrom: 90, redTo: 100,
          yellowFrom:75, yellowTo: 90,
          minorTicks: 5
        };

        var chart = new google.visualization.Gauge(document.getElementById('chart_div'));
        chart.draw(data, options);
</script>
</head>

<body>
            <header class="header">
        <h1>Hydroponic Monitoring Station</h1>
        <form method="get">
            <input type="number" name="readingsCount" min="1" placeholder="Number of readings (<?php echo $readings_count; ?>)">
            <input type="submit" value="UPDATE">
        </form>


    <p>Last reading: <?php echo $last_reading_time; ?></p>
    <section class="content">
        <div id="chart_div" style="width: 400px; height: 120px;"></div>

           <table cellspacing="5" cellpadding="5">
                <tr>
                    <th colspan="3">Average for the last <?php echo $readings_count; ?> readings</th>
               </tr>
                 <tr>
                    <p>
                    <th>Temperature</th>
                    <th>Humidity</th>
                    <th>Pressure</th>
                    <th>Ph</th>
                    <th>RPO</th>
                    <th>EC</th>
                    </p>
                 </tr>

                <tr>
                    <td><?php echo round($avg_temp['avg_amount'], 2); ?> &deg;C</td>
                    <td><?php echo round($avg_humi['avg_amount'], 2); ?> RH</td>
                    <td><?php echo round($avg_press['avg_amount'], 2); ?> Hg</td>
                    <td><?php echo round($avg_ph['avg_amount'],2); ?> %</td>
                    <td><?php echo round($avg_rpo['avg_amount'], 2); ?> %</td>
                    <td><?php echo round($avg_ec['avg_amount'], 2); ?> %</td>                    
                </tr>
            </table>
        </div>
    </section>
<?php
    echo   '<h2> View Latest ' . $readings_count . ' Readings</h2>
            <table cellspacing="5" cellpadding="5" id="tableReadings">
                <tr>
                    <th>ID</th>
                    <th>Sensor</th>
                    <th>Location</th>
                    <th>Value Raw</th>
                    <th>Value 2</th>
                    <th>Timestamp</th>
                </tr>';

    $result = getAllReadings($readings_count);
        if ($result) {
        while ($row = $result->fetch_assoc()) {
            $row_sensor = $row["sensor"];
            $row_location = $row["location"];
            $row_value1 = $row["dblvalueraw"];
            $row_value2 = $row["value2"];
            $row_reading_time = $row["reading_time"];
            // Uncomment to set timezone to - 1 hour (you can change 1 to any number)
            //$row_reading_time = date("Y-m-d H:i:s", strtotime("$row_reading_time - 1 hours"));
            // Uncomment to set timezone to + 7 hours (you can change 7 to any number)
            $row_reading_time = date("Y-m-d H:i:s", strtotime("$row_reading_time + 7 hours"));

            echo '<tr>
                     <td>' . $row_sensor . '</td>
                    <td>' . $row_location . '</td>
                    <td>' . $row_value1 . '</td>
                    <td>' . $row_value2 . '</td>
                    <td>' . $row_reading_time . '</td>
                  </tr>';
        }
        echo '</table>';
        $result->free();
    }
?>
</html>
