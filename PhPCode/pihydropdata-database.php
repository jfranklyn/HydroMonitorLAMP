<!--
  John Franklyn 06/07/20
  Database functions modified added WHERE clauses to search for specific sensors and locations.
-->
<?php
  $servername = "localhost";

  // REPLACE with your Database name
  $dbname = "pihydropdata";
  // REPLACE with Database user
  $username = "pihydrop-user";
  // REPLACE with Database user password
  $password = "Jaf_10205!";

  function insertReading($sensor, $location, $dblvalue_raw, $value2) {
    global $servername, $username, $password, $dbname;

    // Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);
    // Check connection
    if ($conn->connect_error) {
      die("Connection failed: " . $conn->connect_error);
    }

    $sql = "INSERT INTO SensorData (sensor, location, dblvalue_raw, value2)
    VALUES ('" . $sensor . "', '" . $location . "', '" . $dblvalue_raw . "', '" . $value2 . "')";

    if ($conn->query($sql) === TRUE) {
      return "New record created successfully";
    }
    else {
      return "Error: " . $sql . "<br>" . $conn->error;
    }
    $conn->close();
  }
  
  function getAllReadings($limit) {
    global $servername, $username, $password, $dbname;

    // Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);
    // Check connection
    if ($conn->connect_error) {
      die("Connection failed: " . $conn->connect_error);
    }

    $sql = "SELECT id, sensor, location, dblvalueraw, value2, reading_time FROM SensorData order by reading_time desc limit " . $limit;
    if ($result = $conn->query($sql)) {
      return $result;
    }
    else {
      return false;
    }
    $conn->close();
  }
  function getLastReadings($sensor, $location) {
  //function getLastReadings() {      
    global $servername, $username, $password, $dbname;

    // Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);
    // Check connection
    if ($conn->connect_error) {
      die("Connection failed: " . $conn->connect_error);
    }

    $sql = "SELECT id, sensor, location, dblvalueraw, value2, reading_time FROM SensorData WHERE sensor='" . $sensor . "' AND location='" . $location . "' order by reading_time desc limit 1;" ;
//    $sql = "SELECT id, sensor, location, dblvalueraw, value2, reading_time FROM SensorData order by reading_time desc limit 1;" ;
    
        //echo "sql = $sql <br>";
    if ($result = $conn->query($sql)) {
      return $result->fetch_assoc();
    }
    else {
      return false;
    }
    $conn->close();
  }

  function minReading($limit, $value, $sensor, $location) {
     global $servername, $username, $password, $dbname;

    // Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);
    // Check connection
    if ($conn->connect_error) {
      die("Connection failed: " . $conn->connect_error);
    }

    $sql = "SELECT MIN(" . $value . ") AS min_amount FROM (SELECT " . $value . " FROM SensorData WHERE sensor='" . $sensor . "' AND location='" . $location . "' order by reading_time desc limit " . $limit . ") AS min;";

    if ($result = $conn->query($sql)) {
      return $result->fetch_assoc();
    }
    else {
      return false;
    }
    $conn->close();
  }

  function maxReading($limit, $value, $sensor, $location) {
     global $servername, $username, $password, $dbname;

    // Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);
    // Check connection
    if ($conn->connect_error) {
      die("Connection failed: " . $conn->connect_error);
    }

    $sql = "SELECT MAX(" . $value . ") AS max_amount FROM (SELECT " . $value . " FROM SensorData WHERE sensor='" . $sensor . "' AND location='" . $location . "' order by reading_time desc limit " . $limit . ") AS max";
             //echo "sql = $sql <br>";     
    if ($result = $conn->query($sql)) {
      return $result->fetch_assoc();
    }
    else {
      return false;
    }
    $conn->close();
  }

  function avgReading($limit, $value, $sensor, $location) {
     global $servername, $username, $password, $dbname;

    // Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);
    // Check connection
    if ($conn->connect_error) {
      die("Connection failed: " . $conn->connect_error);
    }

    $sql = "SELECT AVG(" . $value . ") AS avg_amount FROM (SELECT " . $value . " FROM SensorData WHERE sensor='" . $sensor . "' AND location='" . $location . "' order by reading_time desc limit " . $limit . ") AS avg";
    if ($result = $conn->query($sql)) {
      return $result->fetch_assoc();
    }
    else {
      return false;
    }
    $conn->close();
  }
?>
