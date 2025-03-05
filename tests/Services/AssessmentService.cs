using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using YourNamespace.Models;

namespace YourNamespace.Services
{
    public class AssessmentService
    {
        private readonly ICategoryService _categoryService;
        private readonly ILogger _logger;

        public AssessmentService(ICategoryService categoryService, ILogger logger)
        {
            _categoryService = categoryService ?? throw new ArgumentNullException(nameof(categoryService));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
        }

        /// <summary>
        /// Gets all assessments for an employee asynchronously
        /// </summary>
        public async Task<List<UnifiedAssessmentViewModel>> GetAllAssessmentsAsync(
            Dictionary<string, object> employee,
            string performanceReviewName,
            string agreedCommentName,
            List<Rating> ratings,
            object performanceFilter)
        {
            try
            {
                var unifiedAssessments = new List<UnifiedAssessmentViewModel>();
                var assessmentTypes = new Dictionary<string, (string Category, string ItemName)>
                {
                    { "General Work", (CategoryMappings.GeneralWork.NonNECAudit, "General Work Item: General Work Item Name") },
                    { "Teamwork", (CategoryMappings.Teamwork.NonNECAudit, "Teamwork Item: Teamwork Item Name") },
                    { "Leadership", (CategoryMappings.Leadership.NonNECAudit, "Leadership Item: Leadership Item Name") },
                    { "Strategy", (CategoryMappings.Strategy.NonNECAudit, "Strategy Item: Strategy Item Name") },
                    { "Communication", (CategoryMappings.Communication.NonNECAudit, "Communication Item: Communication Item Name") }
                };

                foreach (var assessmentType in assessmentTypes)
                {
                    try
                    {
                        var items = await _categoryService.ReadAsync(
                            assessmentType.Value.Category,
                            null,
                            performanceFilter,
                            null,
                            null,
                            true);

                        foreach (var item in items)
                        {
                            var assessment = CreateAssessmentViewModel(
                                item,
                                assessmentType.Key,
                                assessmentType.Value.ItemName,
                                employee,
                                performanceReviewName,
                                agreedCommentName,
                                ratings);

                            unifiedAssessments.Add(assessment);
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.Error($"Error processing {assessmentType.Key} assessment", ex);
                        throw new AssessmentProcessingException(
                            $"Failed to process {assessmentType.Key} assessment",
                            ex);
                    }
                }

                return unifiedAssessments;
            }
            catch (Exception ex)
            {
                _logger.Error("Error getting all assessments", ex);
                throw new AssessmentProcessingException("Failed to get all assessments", ex);
            }
        }

        private UnifiedAssessmentViewModel CreateAssessmentViewModel(
            Dictionary<string, object> item,
            string assessmentType,
            string itemNameField,
            Dictionary<string, object> employee,
            string performanceReviewName,
            string agreedCommentName,
            List<Rating> ratings)
        {
            if (item == null) throw new ArgumentNullException(nameof(item));
            if (employee == null) throw new ArgumentNullException(nameof(employee));

            var assessment = new UnifiedAssessmentViewModel
            {
                DataEntityID = Convert.ToInt64(item["DataEntityID"]),
                AssessmentItem = item[itemNameField].ToString(),
                PerformanceReview = Convert.ToInt64(item[performanceReviewName]),
                Employee = FormatEmployeeName(employee),
                Date = DateTime.Now,
                AgreedRating = 0,
                Ratings = ratings,
                AssessmentType = assessmentType
            };

            if (item.TryGetValue(agreedCommentName, out object value) && value != null)
            {
                assessment.AgreedComments = value.ToString();
            }

            return assessment;
        }

        private string FormatEmployeeName(Dictionary<string, object> employee)
        {
            return $"({employee["Employee Number"]}) {employee["First Name"]} {employee["Surname"]}";
        }
    }

    public class AssessmentProcessingException : Exception
    {
        public AssessmentProcessingException(string message, Exception innerException)
            : base(message, innerException)
        {
        }
    }
}