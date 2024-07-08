import azure.functions as func
import logging
import requests
import json
import pyodbc
from datetime import datetime
import os
import folium

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
# Get the connection string from environment variable
sqldb_connectionstring = os.getenv("sqldb_connection")


@app.route(route="http_trigger")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
	logging.info('Python HTTP trigger function processed a request.')
	# Create a new connection
	conn = pyodbc.connect(sqldb_connectionstring)
	# Create a new cursor
	cursor = conn.cursor()
	name = req.params.get('name')
	proceso = req.params.get('proceso')

	if not name:
		try:
			req_body = req.get_json()
		except ValueError:
			pass
		else:
			name = req_body.get('name')
			
	if name and proceso:
		paradas = get_paradas(int(name))
		for i in paradas:
			#INSERT into SQL Server table Lineas (Linea, Parada, Tiempo) VALUES (name, i, tiempo_est)
			cursor.execute("INSERT INTO Tiempos (ParadaID, Tiempo, Timestamp, ProcesoID) VALUES (?, ?, ?, ?) ", i,get_tiempos(int(i),int(name)), datetime.now(), proceso)
			# Commit the transaction
			conn.commit()
		return func.HttpResponse(f"Se ha insertado correctamente en la base de datos {proceso} para la linea {name}.")
	else:
		return func.HttpResponse(
			"This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
			status_code=200
		)
        
def get_tiempos(paradaNo, linea=-1):
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
		"Accept-Encoding": "gzip, deflate",
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
		"DNT": "1",
		"Connection": "close",
		"Upgrade-Insecure-Requests": "1"
	}
	response = requests.get('https://movil.titsa.com/ajax/jsonguaguasparadadestino.php?IdParada=' + str(paradaNo),
							headers=headers)  # , proxies=proxies)

	try:
		# Attempt to parse the string as JSON
		parsed_json = json.loads(response.content)
		# Indent for readability (default is 4 spaces)
		indent = 4

		# Use dumps to convert the parsed JSON object back to a formatted string with linejumps
		json.dumps(parsed_json, indent=indent)
		# print("Successfully parsed JSON:")
		# print(formatted_json)
		# Create an empty list to store the id-tiempo pairs
		id_tiempo_pairs = []

		# Iterate over the "tiempos" list
		for tiempo in parsed_json["tiempos"]:
			# Extract the "id" and "tiempo" values
			id = tiempo["id"]
			tiempo_value = tiempo["tiempo"]

			# Check if "id" matches the desired value
			if int(id) == linea:
				# Print the "tiempo" value
				return int(tiempo_value)  # Exit the loop after finding a match
			else:
				# Create a dictionary to store the pair
				id_tiempo_pair = {"id": id, "tiempo": tiempo_value}

				# Append the pair to the list
				id_tiempo_pairs.append(id_tiempo_pair)
		print("Queda mucho tiempo para la siguiente guagua, el resto de guaguas son.")
		return id_tiempo_pairs

	except json.JSONDecodeError as e:
		print("Error parsing JSON:", e)
		# Handle the parsing error (e.g., log the error or return an empty object)

def get_paradas(LineaNo):
	"""
	The function `get_paradas` retrieves bus stop codes for a specific bus line using a provided
	LineaNo.
	
	:param LineaNo: The `get_paradas` function you provided seems to be a Python function that makes a
	request to a specific URL, parses the JSON response, and extracts the "codigo" values from each bus
	stop ("parada")
	:return: The `get_paradas` function returns a list of bus stop codes for a given bus line number.
	The function makes a request to a specific URL with the provided line number and trayecto ID, then
	parses the JSON response to extract the "codigo" values from each bus stop. Finally, it returns a
	list of these bus stop codes.
	"""
	headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}
	response = requests.get('https://titsa.com/ajax/xItinerario.php?c=1234&id_linea=' + str(LineaNo) + '&id_trayecto=' + str(11), headers=headers)#, proxies=proxies)

	try:
		# Attempt to parse the string as JSON
		parsed_json = json.loads(response.content)
		# Indent for readability (default is 4 spaces)
		indent = 4

		# Use dumps to convert the parsed JSON object back to a formatted string with linejumps
		formatted_json = json.dumps(parsed_json, indent=indent)
		#print("Successfully parsed JSON:")
		#print(formatted_json)
		# Extract the "codigo" values from each parada (bus stop)
		codigo_list = []
		for parada in parsed_json["paradas"]:
			codigo_list.append(int(parada["codigo"]))
		return codigo_list
	except json.JSONDecodeError as e:
		print("Error parsing JSON:", e)
		# Handle the parsing error (e.g., log the error or return an empty object)

@app.route(route="mostrar_html")
def mostrar_html(req: func.HttpRequest) -> func.HttpResponse:
	logging.info('Python HTTP trigger function processed a request.')

	name = req.params.get('name')
	if not name:
		try:
			req_body = req.get_json()
		except ValueError:
			pass
		else:
			name = req_body.get('name')

	if name:
		return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
	else:
		# Connect to SQL Server
		conn = pyodbc.connect("Driver={ODBC Driver 18 for SQL Server};Server=tcp:servidorcloudcomputing.database.windows.net,1433;Database=ProyectoFinal;Uid=CloudSAc56aa020;Pwd=Asdf123.;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;")
		cursor = conn.cursor()

		# Execute custom SQL query
		query = """WITH LastProcesos AS (
			SELECT DISTINCT TOP 2 ProcesoID  -- Get last 10 distinct ProcesoIDs (adjust as needed)
			FROM Tiempos
			ORDER BY ProcesoID DESC
			)
			SELECT T.*, P.NumLinea, S.stop_lat, S.stop_lon
			FROM Tiempos T
			JOIN Procesos P ON T.ProcesoID = P.ID
			JOIN LastProcesos LP ON T.ProcesoID = LP.ProcesoID
			JOIN stops S ON T.ParadaID = S.stop_id   -- Join with stops table
			ORDER BY T.ID DESC;
				"""
		cursor.execute(query)
		rows = cursor.fetchall()

		# Assuming 'row' is a tuple where the first element determines visibility
		table = "<table id='dataTable'>"
		for row in rows:
			table += "<tr>"
			for col in row:
				table += f"<td>{col}</td>"
			table += "</tr>"
		table += "</table>"

		# Create a folium map

		# Set the center of the map
		m = folium.Map(location=[28.473162, -16.280214], zoom_start=12)

		# Iterate over the rows and add markers to the map
		for row in rows:
			stop_lat = row[6] / 10000  # Adjust this index based on the column index of stop_lat
			stop_lon = row[7] / 10000  # Adjust this index based on the column index of stop_lon
			stop_time = row[2]  # Adjust this index based on the column index of stop_time
			stop_id = row[1]  # Adjust this index based on the column index of stop_id

			# Determine the marker color based on the value of row[5]
			if row[5] == 14:
				marker_color = "blue"
			elif row[5] == 15:
				marker_color = "green"
			else:
				marker_color = "red"  # Default color if row[5] is neither 14 nor 15

			# Add a marker to the map with the determined color
			folium.Marker(
				location=[stop_lat, stop_lon],
				popup=f"Parada: {stop_id}<br>Tiempo: {stop_time} minutos",
				icon=folium.Icon(color=marker_color)
			).add_to(m)

		# Create a temporary file to store the map HTML
		with open("/tmp/map.html", "w") as f:
			f.write(m._repr_html_())

		# Read the contents of the temporary file
		with open("/tmp/map.html", "r") as f:
			map_html = f.read()

		return func.HttpResponse(
			f"""
			<html>
			<head>
				<title>Table Data</title>
				<style>
				.container {{
					display: flex;
					flex-direction: row;
				}}
				
				.table-container {{
					width: 30%;
				}}
				
				.map-container {{
					width: 70%;
				}}
				
				table {{
					border-collapse: collapse;
					width: 100%;
				}}
				
				th, td {{
					text-align: left;
					padding: 8px;
				}}
				
				tr:nth-child(even) {{
					background-color: #f2f2f2;
				}}
				
				.column-title {{
					font-weight: bold;
				}}
				</style>
			</head>
			<body>
				<h1>Ultimos datos de las paradas</h1>
				<div class="container">
					<div class="table-container">
						<table id="dataTable">
							<tr>
								<th class="column-title">ID</th>
								<th class="column-title">ParadaID</th>
								<th class="column-title">Tiempo</th>
								<th class="column-title">Timestamp</th>
								<th class="column-title">ProcesoID</th>
								<th class="column-title">NumLinea</th>
								<th class="column-title">stop_lat</th>
								<th class="column-title">stop_lon</th>
							</tr>
							{table} <!-- Make sure this table has the id 'dataTable' -->
						</table>
					</div>
					<div class="map-container">
						<div id="map">{map_html}</div> <!-- Display the map -->
					</div>
				</div>
			</body>
			</html>
			""",
			status_code=200,
			headers={"Content-Type": "text/html"}
		)
