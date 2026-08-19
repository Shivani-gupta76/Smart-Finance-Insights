from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

from extensions import db
from models.goal import Goal
from models.goal_part import GoalPart


goal = Blueprint(
    "goal",
    __name__
)


# =========================================================
# VIEW + ADD GOAL
# =========================================================

@goal.route("/goals", methods=["GET", "POST"])
@login_required
def goals():

    # -----------------------------------------------------
    # ADD GOAL
    # -----------------------------------------------------

    if request.method == "POST":

        goal_name = request.form.get("goal_name")
        goal_type = request.form.get("goal_type")
        

        target_amount = float(
            request.form.get("target_amount") or 0
        )

        current_amount = float(
            request.form.get("current_amount") or 0
        )

        target_date = request.form.get("target_date")

        category = request.form.get("category")
        priority = request.form.get("priority")

        # HTML form uses "description"
        # Database/model field is "notes"
        
        notes = request.form.get("notes")
        


        # -------------------------------------------------
        # Determine Status
        # -------------------------------------------------

        if (
            target_amount > 0
            and current_amount >= target_amount
        ):
            status = "Completed"
        else:
            status = "In Progress"


        # -------------------------------------------------
        # Create Goal
        # -------------------------------------------------

        new_goal = Goal(

            goal_name=goal_name,

            goal_type=goal_type,

            target_amount=target_amount,

            current_amount=current_amount,

            target_date=datetime.strptime(
                target_date,
                "%Y-%m-%d"
            ).date(),

            category=category,

            priority=priority,

            status=status,

            notes=notes,

            user_id=current_user.id
        )


        db.session.add(new_goal)

        db.session.commit()


        flash(
            "Financial goal added successfully!",
            "success"
        )


        return redirect(
            url_for("goal.goals")
        )


    # =====================================================
    # GET USER GOALS
    # =====================================================

    goals = Goal.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Goal.target_date.asc()
    ).all()


    # =====================================================
    # GOAL SUMMARY
    # =====================================================

    total_goals = len(goals)

    completed_goals = 0

    active_goals = 0


    # =====================================================
    # CALCULATE GOAL PROGRESS
    # =====================================================

    for item in goals:

        # -------------------------------------------------
        # Progress
        # -------------------------------------------------

        if item.target_amount > 0:

            item.progress = round(
                (
                    item.current_amount
                    / item.target_amount
                ) * 100,
                2
            )

        else:

            item.progress = 0


        # -------------------------------------------------
        # Maximum 100%
        # -------------------------------------------------

        if item.progress > 100:

            item.progress = 100


        # -------------------------------------------------
        # Remaining Amount
        # -------------------------------------------------

        item.remaining_amount = max(
            item.target_amount
            - item.current_amount,
            0
        )


        # -------------------------------------------------
        # Status
        # -------------------------------------------------

        if (
            item.target_amount > 0
            and item.current_amount
            >= item.target_amount
        ):

            item.status = "Completed"

            completed_goals += 1

        else:

            item.status = "In Progress"

            active_goals += 1


    # =====================================================
    # RENDER GOALS PAGE
    # =====================================================

    return render_template(
        "goals.html",

        goals=goals,

        total_goals=total_goals,

        active_goals=active_goals,

        completed_goals=completed_goals
    )

 # =========================================================
# GOAL DETAILS
# =========================================================

@goal.route(
    "/goals/<int:id>/details",
    methods=["GET", "POST"]
)
@login_required
def goal_details(id):

    goal_data = Goal.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    # -----------------------------------------------------
    # ADD GOAL PART
    # -----------------------------------------------------

    if request.method == "POST":

        part_name = request.form.get("part_name", "").strip()

        step_order = int(
            request.form.get("step_order") or 1
        )

        description = request.form.get(
            "description"
        )

        estimated_cost = float(
            request.form.get("estimated_cost") or 0
        )

        actual_cost = float(
            request.form.get("actual_cost") or 0
        )

        start_date = request.form.get(
            "start_date"
        )

        completion_date = request.form.get(
            "completion_date"
        )

        notes = request.form.get("notes")

        # -------------------------------------------------
        # Determine status
        # -------------------------------------------------

        if completion_date:
            status = "Completed"

        elif actual_cost > 0:
            status = "In Progress"

        else:
            status = "Pending"

        # -------------------------------------------------
        # Create Goal Part
        # -------------------------------------------------

        new_part = GoalPart(
            goal_id=goal_data.id,

            part_name=part_name,

            step_order=step_order,

            description=description,

            estimated_cost=estimated_cost,

            actual_cost=actual_cost,

            start_date=(
                datetime.strptime(
                    start_date,
                    "%Y-%m-%d"
                ).date()
                if start_date
                else None
            ),

            completion_date=(
                datetime.strptime(
                    completion_date,
                    "%Y-%m-%d"
                ).date()
                if completion_date
                else None
            ),

            status=status,

            notes=notes
        )

        db.session.add(new_part)
        db.session.commit()

        flash(
            "Goal part added successfully!",
            "success"
        )

        return redirect(
            url_for(
                "goal.goal_details",
                id=goal_data.id
            )
        )

    # -----------------------------------------------------
    # GET GOAL PARTS
    # -----------------------------------------------------

    parts = GoalPart.query.filter_by(
        goal_id=goal_data.id
    ).order_by(
        GoalPart.step_order.asc()
    ).all()

    # -----------------------------------------------------
    # CHECK IF A PART IS BEING EDITED
    # -----------------------------------------------------

    edit_part_id = request.args.get(
        "edit_part",
        type=int
    )

    edit_part = None

    if edit_part_id:

        edit_part = GoalPart.query.filter_by(
            id=edit_part_id,
            goal_id=goal_data.id
        ).first()

    # -----------------------------------------------------
    # PART STATISTICS
    # -----------------------------------------------------

    total_parts = len(parts)

    completed_parts = sum(
        1
        for part in parts
        if part.status == "Completed"
    )

    in_progress_parts = sum(
        1
        for part in parts
        if part.status == "In Progress"
    )

    pending_parts = sum(
        1
        for part in parts
        if part.status == "Pending"
    )

    # -----------------------------------------------------
    # COST CALCULATIONS
    # -----------------------------------------------------

    estimated_total = sum(
        part.estimated_cost or 0
        for part in parts
    )

    actual_total = sum(
        part.actual_cost or 0
        for part in parts
    )

    cost_variance = (
        estimated_total - actual_total
    )

    # -----------------------------------------------------
    # PART PROGRESS
    # -----------------------------------------------------

    if total_parts > 0:

        part_progress = round(
            (
                completed_parts
                / total_parts
            ) * 100,
            2
        )

    else:

        part_progress = 0

    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

    return render_template(
        "goal_details.html",

        goal=goal_data,

        parts=parts,

        total_parts=total_parts,

        completed_parts=completed_parts,

        in_progress_parts=in_progress_parts,

        pending_parts=pending_parts,

        estimated_total=estimated_total,

        actual_total=actual_total,

        cost_variance=cost_variance,

        part_progress=part_progress,

        edit_part=edit_part
    )
# =========================================================
# EDIT GOAL PART
# =========================================================

@goal.route(
    "/goals/parts/edit/<int:part_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_goal_part(part_id):

    part = GoalPart.query.get_or_404(part_id)

    # Make sure this part belongs to the logged-in user's goal
    goal_data = Goal.query.filter_by(
        id=part.goal_id,
        user_id=current_user.id
    ).first_or_404()

    # -----------------------------
    # SAVE EDITED PART
    # -----------------------------

    if request.method == "POST":

        part_name = request.form.get("part_name", "").strip()
        step_order = request.form.get("step_order", "").strip()

        estimated_cost = request.form.get(
            "estimated_cost",
            "0"
        ).strip()

        actual_cost = request.form.get(
            "actual_cost",
            "0"
        ).strip()

        start_date = request.form.get(
            "start_date",
            ""
        ).strip()

        completion_date = request.form.get(
            "completion_date",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        # -----------------------------
        # Basic validation
        # -----------------------------

        if not part_name:
            flash(
                "Part name is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "goal.edit_goal_part",
                    part_id=part.id
                )
            )

        # -----------------------------
        # Convert numeric values
        # -----------------------------

        try:
            part.step_order = int(step_order or 1)
            part.estimated_cost = float(
                estimated_cost or 0
            )
            part.actual_cost = float(
                actual_cost or 0
            )

        except ValueError:

            flash(
                "Please enter valid numeric values.",
                "danger"
            )

            return redirect(
                url_for(
                    "goal.edit_goal_part",
                    part_id=part.id
                )
            )

        # -----------------------------
        # Update text fields
        # -----------------------------

        part.part_name = part_name
        part.description = description or None
        part.notes = notes or None

        # -----------------------------
        # Update dates
        # -----------------------------

        if start_date:
            part.start_date = datetime.strptime(
                start_date,
                "%Y-%m-%d"
            ).date()
        else:
            part.start_date = None

        if completion_date:
            part.completion_date = datetime.strptime(
                completion_date,
                "%Y-%m-%d"
            ).date()
        else:
            part.completion_date = None

        # -----------------------------
        # Save
        # -----------------------------

        db.session.commit()

        flash(
            "Goal part updated successfully!",
            "success"
        )

        return redirect(
            url_for(
                "goal.goal_details",
                id=goal_data.id
            )
        )

    # -----------------------------
    # SHOW EDIT FORM
    # -----------------------------

    return render_template(
    "edit_goal_part.html",
    goal=goal_data,
    part=part
)

    # =========================================================
# DELETE GOAL PART
# =========================================================

@goal.route(
    "/goals/parts/delete/<int:id>",
    methods=["POST"]
)
@login_required
def delete_goal_part(id):

    part = GoalPart.query.get_or_404(id)

    goal_data = Goal.query.filter_by(
        id=part.goal_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(part)
    db.session.commit()

    flash(
        "Goal part deleted successfully!",
        "success"
    )

    return redirect(
        url_for(
            "goal.goal_details",
            id=goal_data.id
        )
    )

    # =========================================================
# UPDATE GOAL PART STATUS
# =========================================================

@goal.route(
    "/goals/parts/status/<int:id>",
    methods=["POST"]
)
@login_required
def update_goal_part_status(id):

    part = GoalPart.query.get_or_404(id)

    goal_data = Goal.query.filter_by(
        id=part.goal_id,
        user_id=current_user.id
    ).first_or_404()

    new_status = request.form.get("status")

    if new_status in [
        "Pending",
        "In Progress",
        "Completed"
    ]:

        part.status = new_status

        if new_status == "Completed":
            part.completion_date = datetime.utcnow().date()

        elif new_status != "Completed":
            part.completion_date = None

        db.session.commit()

        flash(
            "Goal part status updated!",
            "success"
        )

    return redirect(
        url_for(
            "goal.goal_details",
            id=goal_data.id
        )
    )


# =========================================================
# EDIT GOAL
# =========================================================

@goal.route(
    "/goals/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_goal(id):

    goal_data = Goal.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()


    # -----------------------------------------------------
    # UPDATE GOAL
    # -----------------------------------------------------

    if request.method == "POST":

        goal_data.goal_name = request.form.get(
            "goal_name"
        )


        goal_data.goal_type = request.form.get(
            "goal_type"
        )


        goal_data.target_amount = float(
            request.form.get("target_amount") or 0
        )


        goal_data.current_amount = float(
            request.form.get("current_amount") or 0
        )


        goal_data.target_date = datetime.strptime(
            request.form.get("target_date"),
            "%Y-%m-%d"
        ).date()


        goal_data.category = request.form.get(
            "category"
        )


        goal_data.priority = request.form.get(
            "priority"
        )


        goal_data.notes = request.form.get(
            "notes"
        )


        # -------------------------------------------------
        # Update Status
        # -------------------------------------------------

        if (
            goal_data.target_amount > 0
            and goal_data.current_amount
            >= goal_data.target_amount
        ):

            goal_data.status = "Completed"

        else:

            goal_data.status = "In Progress"


        db.session.commit()


        flash(
            "Financial goal updated successfully!",
            "success"
        )


        return redirect(
            url_for("goal.goals")
        )


    # -----------------------------------------------------
    # EDIT PAGE
    # -----------------------------------------------------

    return render_template(
        "edit_goal.html",
        goal=goal_data
    )


# =========================================================
# DELETE GOAL
# =========================================================

@goal.route(
    "/goals/delete/<int:id>"
)
@login_required
def delete_goal(id):

    goal_data = Goal.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()


    db.session.delete(
        goal_data
    )

    db.session.commit()


    flash(
        "Financial goal deleted successfully!",
        "success"
    )


    return redirect(
        url_for("goal.goals")
    )