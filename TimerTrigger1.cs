using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Host;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;

namespace Company.Function
{
    public class TimerTrigger1
    {
        private static readonly HttpClient client = new HttpClient();

        [FunctionName("TimerTrigger1")]
        public async Task Run([TimerTrigger("0 0 */5 * * *")]TimerInfo myTimer, ILogger log)
        {
            log.LogInformation($"C# Timer trigger function executed at: {DateTime.Now}");

            // Replace with the URL of your HttpTrigger1 function
            string functionUrl = "https://pruebacuatro.azurewebsites.net/api/AddTest1?code=7GlTm2ZYqjodPZgRHE6KdaGzJQE63hfDSzHcDjqGOQhSAzFu8BtUnA%3D%3D";

            // Trigger HttpTrigger1 with name=15
            var content = new StringContent(JsonConvert.SerializeObject(new { name = "15" }), Encoding.UTF8, "application/json");
            var response = await client.PostAsync(functionUrl, content);
            log.LogInformation($"Triggered HttpTrigger1 with name=15, response status: {response.StatusCode}");
            await Task.Delay(30000);
            // Trigger HttpTrigger1 with name=14
            content = new StringContent(JsonConvert.SerializeObject(new { name = "14" }), Encoding.UTF8, "application/json");
            response = await client.PostAsync(functionUrl, content);
            log.LogInformation($"Triggered HttpTrigger1 with name=14, response status: {response.StatusCode}");
        }
    }
}