using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Web.Mvc;
using YourNamespace.Models;
using YourNamespace.Services;

namespace YourNamespace.Controllers
{
    public class DashboardController : Controller
    {
        private readonly IAssessmentService _assessmentService;
        private readonly ILogger _logger;

        public DashboardController(IAssessmentService assessmentService, ILogger logger)
        {
            _assessmentService = assessmentService ?? throw new ArgumentNullException(nameof(assessmentService));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
        }

        /// <summary>
        /// Displays the unified manager rating view
        /// </summary>
        [HttpGet]
        public async Task<ActionResult> Index()
        {
            try
            {
                var assessments = await _assessmentService.GetAllAssessmentsAsync(
                    Employee,
                    PerformanceReviewName,
                    AgreedCommentName,
                    GetRatings,
                    PerformanceFilter);

                return View("UnifiedManagerRating", assessments);
            }
            catch (AssessmentProcessingException ex)
            {
                _logger.Error("Error processing assessments", ex);
                TempData["ErrorMessage"] = "An error occurred while processing assessments. Please try again.";
                return RedirectToAction("Error");
            }
            catch (Exception ex)
            {
                _logger.Error("Unexpected error in Index action", ex);
                TempData["ErrorMessage"] = "An unexpected error occurred. Please contact support.";
                return RedirectToAction("Error");
            }
        }

        /// <summary>
        /// Updates the agreed rating for an assessment
        /// </summary>
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<JsonResult> SetUnifiedAgreedRating(long assessmentId, int ratingId)
        {
            try
            {
                if (ratingId < 1 || ratingId > 5)
                {
                    return Json(new { success = false, message = "Invalid rating value" });
                }

                await _assessmentService.UpdateAgreedRatingAsync(assessmentId, ratingId);
                return Json(new { success = true });
            }
            catch (Exception ex)
            {
                _logger.Error($"Error updating rating for assessment {assessmentId}", ex);
                return Json(new { success = false, message = "Failed to update rating" });
            }
        }

        /// <summary>
        /// Updates the agreed comment for an assessment
        /// </summary>
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<JsonResult> SetUnifiedAgreedComment(long assessmentId, string comments)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(comments))
                {
                    return Json(new { success = false, message = "Comments cannot be empty" });
                }

                await _assessmentService.UpdateAgreedCommentAsync(assessmentId, comments);
                return Json(new { success = true });
            }
            catch (Exception ex)
            {
                _logger.Error($"Error updating comments for assessment {assessmentId}", ex);
                return Json(new { success = false, message = "Failed to update comments" });
            }
        }

        /// <summary>
        /// Displays the error view
        /// </summary>
        public ActionResult Error()
        {
            return View();
        }
    }
}