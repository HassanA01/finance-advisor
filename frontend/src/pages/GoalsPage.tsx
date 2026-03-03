import {
  Calendar,
  CheckCircle2,
  Loader2,
  Pause,
  Pencil,
  Play,
  Plus,
  Target,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";

import { goalApi, type GoalResponse } from "@/lib/api";

function GoalProgress({ current, target }: { current: number; target: number }) {
  const pct = target > 0 ? Math.min((current / target) * 100, 100) : 0;
  const isComplete = pct >= 100;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-white/50 tabular-nums">
          ${current.toLocaleString()} of ${target.toLocaleString()}
        </span>
        <span
          className={
            isComplete ? "text-emerald-400 font-medium" : "text-white/30"
          }
        >
          {pct.toFixed(0)}%
        </span>
      </div>
      <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${
            isComplete
              ? "bg-gradient-to-r from-emerald-500 to-emerald-400"
              : "bg-gradient-to-r from-amber-500/70 to-amber-400"
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function GoalDialog({
  goal,
  onClose,
  onSave,
}: {
  goal: GoalResponse | null;
  onClose: () => void;
  onSave: (data: {
    name: string;
    target_amount: number;
    current_amount?: number;
    deadline?: string;
  }) => void;
}) {
  const [name, setName] = useState(goal?.name || "");
  const [targetAmount, setTargetAmount] = useState(
    goal?.target_amount?.toString() || ""
  );
  const [currentAmount, setCurrentAmount] = useState(
    goal?.current_amount?.toString() || "0"
  );
  const [deadline, setDeadline] = useState(
    goal?.deadline ? goal.deadline.split("T")[0] : ""
  );
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !targetAmount) return;
    setSaving(true);
    const data: {
      name: string;
      target_amount: number;
      current_amount?: number;
      deadline?: string;
    } = {
      name: name.trim(),
      target_amount: parseFloat(targetAmount),
    };
    if (goal) data.current_amount = parseFloat(currentAmount || "0");
    if (deadline) data.deadline = `${deadline}T00:00:00`;
    onSave(data);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative w-full max-w-md mx-4 p-6 rounded-xl bg-[#141416] border border-white/[0.08] shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-white/80 font-medium">
            {goal ? "Edit Goal" : "New Goal"}
          </h3>
          <button
            onClick={onClose}
            className="text-white/20 hover:text-white/50 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-white/40 text-xs uppercase tracking-wider block mb-1.5">
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Emergency Fund"
              required
              className="w-full px-3 py-2.5 bg-white/[0.04] border border-white/[0.08] rounded-lg text-white/80 text-sm placeholder:text-white/15 focus:outline-none focus:border-amber-500/40"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-white/40 text-xs uppercase tracking-wider block mb-1.5">
                Target ($)
              </label>
              <input
                type="number"
                value={targetAmount}
                onChange={(e) => setTargetAmount(e.target.value)}
                placeholder="5000"
                required
                min="1"
                step="0.01"
                className="w-full px-3 py-2.5 bg-white/[0.04] border border-white/[0.08] rounded-lg text-white/80 text-sm placeholder:text-white/15 focus:outline-none focus:border-amber-500/40"
              />
            </div>
            {goal && (
              <div>
                <label className="text-white/40 text-xs uppercase tracking-wider block mb-1.5">
                  Current ($)
                </label>
                <input
                  type="number"
                  value={currentAmount}
                  onChange={(e) => setCurrentAmount(e.target.value)}
                  min="0"
                  step="0.01"
                  className="w-full px-3 py-2.5 bg-white/[0.04] border border-white/[0.08] rounded-lg text-white/80 text-sm placeholder:text-white/15 focus:outline-none focus:border-amber-500/40"
                />
              </div>
            )}
          </div>

          <div>
            <label className="text-white/40 text-xs uppercase tracking-wider block mb-1.5">
              Deadline (optional)
            </label>
            <input
              type="date"
              value={deadline}
              onChange={(e) => setDeadline(e.target.value)}
              className="w-full px-3 py-2.5 bg-white/[0.04] border border-white/[0.08] rounded-lg text-white/80 text-sm focus:outline-none focus:border-amber-500/40"
            />
          </div>

          <button
            type="submit"
            disabled={saving || !name.trim() || !targetAmount}
            className="w-full py-2.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-[#0a0a0b] font-semibold text-sm rounded-lg transition-all disabled:opacity-50 cursor-pointer"
          >
            {saving ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Saving...
              </span>
            ) : goal ? (
              "Update Goal"
            ) : (
              "Create Goal"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

function DeleteConfirmDialog({
  goalName,
  onClose,
  onConfirm,
}: {
  goalName: string;
  onClose: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative w-full max-w-sm mx-4 p-6 rounded-xl bg-[#141416] border border-white/[0.08] shadow-2xl">
        <h3 className="text-white/80 font-medium mb-2">Delete Goal</h3>
        <p className="text-white/40 text-sm mb-6">
          Are you sure you want to delete &quot;{goalName}&quot;? This cannot be
          undone.
        </p>
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 bg-white/[0.05] border border-white/[0.08] rounded-lg text-white/50 text-sm hover:bg-white/[0.08] transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 py-2.5 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm hover:bg-red-500/30 transition-colors cursor-pointer"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

const STATUS_CONFIG: Record<
  string,
  { label: string; color: string; bg: string }
> = {
  active: { label: "Active", color: "text-amber-400", bg: "bg-amber-500/10" },
  completed: {
    label: "Completed",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
  },
  paused: { label: "Paused", color: "text-white/30", bg: "bg-white/5" },
};

export default function GoalsPage() {
  const [goals, setGoals] = useState<GoalResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogGoal, setDialogGoal] = useState<GoalResponse | null | "new">(
    null
  );
  const [deleteGoal, setDeleteGoal] = useState<GoalResponse | null>(null);

  const fetchGoals = () => {
    goalApi
      .list()
      .then(setGoals)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchGoals();
  }, []);

  const handleSave = async (data: {
    name: string;
    target_amount: number;
    current_amount?: number;
    deadline?: string;
  }) => {
    if (dialogGoal === "new") {
      await goalApi.create(data);
    } else if (dialogGoal) {
      await goalApi.update(dialogGoal.id, data);
    }
    setDialogGoal(null);
    fetchGoals();
  };

  const handleStatusChange = async (goal: GoalResponse, newStatus: string) => {
    await goalApi.update(goal.id, { status: newStatus });
    fetchGoals();
  };

  const handleDelete = async () => {
    if (deleteGoal) {
      await goalApi.delete(deleteGoal.id);
      setDeleteGoal(null);
      fetchGoals();
    }
  };

  const [now] = useState(() => Date.now());
  const activeGoals = goals.filter((g) => g.status === "active");
  const completedGoals = goals.filter((g) => g.status === "completed");
  const pausedGoals = goals.filter((g) => g.status === "paused");

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto py-12 px-6">
        <div className="flex items-center justify-center py-20 text-white/20">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto py-12 px-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-white/90 mb-1">Goals</h1>
          <p className="text-white/40 text-sm">
            {activeGoals.length} active
            {completedGoals.length > 0 &&
              ` · ${completedGoals.length} completed`}
          </p>
        </div>
        <button
          onClick={() => setDialogGoal("new")}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-[#0a0a0b] font-semibold text-sm rounded-lg transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          New Goal
        </button>
      </div>

      {goals.length === 0 ? (
        <div className="text-center py-20 rounded-xl bg-white/[0.02] border border-white/[0.06]">
          <Target className="w-10 h-10 text-white/10 mx-auto mb-3" />
          <p className="text-white/30 text-sm mb-1">No goals yet</p>
          <p className="text-white/15 text-xs">
            Set your first financial goal to start tracking progress
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Active Goals */}
          {activeGoals.length > 0 && (
            <div>
              <h2 className="text-white/40 text-xs uppercase tracking-wider mb-3">
                Active
              </h2>
              <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
                {activeGoals.map((goal) => (
                  <GoalCard
                    key={goal.id}
                    goal={goal}
                    now={now}
                    onEdit={() => setDialogGoal(goal)}
                    onStatusChange={handleStatusChange}
                    onDelete={() => setDeleteGoal(goal)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Paused Goals */}
          {pausedGoals.length > 0 && (
            <div>
              <h2 className="text-white/40 text-xs uppercase tracking-wider mb-3">
                Paused
              </h2>
              <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
                {pausedGoals.map((goal) => (
                  <GoalCard
                    key={goal.id}
                    goal={goal}
                    now={now}
                    onEdit={() => setDialogGoal(goal)}
                    onStatusChange={handleStatusChange}
                    onDelete={() => setDeleteGoal(goal)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Completed Goals */}
          {completedGoals.length > 0 && (
            <div>
              <h2 className="text-white/40 text-xs uppercase tracking-wider mb-3">
                Completed
              </h2>
              <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
                {completedGoals.map((goal) => (
                  <GoalCard
                    key={goal.id}
                    goal={goal}
                    now={now}
                    onEdit={() => setDialogGoal(goal)}
                    onStatusChange={handleStatusChange}
                    onDelete={() => setDeleteGoal(goal)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Dialogs */}
      {dialogGoal && (
        <GoalDialog
          goal={dialogGoal === "new" ? null : dialogGoal}
          onClose={() => setDialogGoal(null)}
          onSave={handleSave}
        />
      )}
      {deleteGoal && (
        <DeleteConfirmDialog
          goalName={deleteGoal.name}
          onClose={() => setDeleteGoal(null)}
          onConfirm={handleDelete}
        />
      )}
    </div>
  );
}

function GoalCard({
  goal,
  now,
  onEdit,
  onStatusChange,
  onDelete,
}: {
  goal: GoalResponse;
  now: number;
  onEdit: () => void;
  onStatusChange: (goal: GoalResponse, status: string) => void;
  onDelete: () => void;
}) {
  const config = STATUS_CONFIG[goal.status] || STATUS_CONFIG.active;
  const daysLeft = goal.deadline
    ? Math.ceil(
        (new Date(goal.deadline).getTime() - now) / (1000 * 60 * 60 * 24)
      )
    : null;

  return (
    <div className="p-5 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:border-white/[0.1] transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-white/80 text-sm font-medium">{goal.name}</h3>
          <span
            className={`inline-flex items-center text-xs mt-1 px-1.5 py-0.5 rounded ${config.bg} ${config.color}`}
          >
            {config.label}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {goal.status === "active" && (
            <>
              <button
                onClick={() => onStatusChange(goal, "completed")}
                title="Mark completed"
                className="p-1.5 rounded-md text-white/15 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors cursor-pointer"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => onStatusChange(goal, "paused")}
                title="Pause"
                className="p-1.5 rounded-md text-white/15 hover:text-white/40 hover:bg-white/[0.05] transition-colors cursor-pointer"
              >
                <Pause className="w-3.5 h-3.5" />
              </button>
            </>
          )}
          {goal.status === "paused" && (
            <button
              onClick={() => onStatusChange(goal, "active")}
              title="Resume"
              className="p-1.5 rounded-md text-white/15 hover:text-amber-400 hover:bg-amber-500/10 transition-colors cursor-pointer"
            >
              <Play className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={onEdit}
            title="Edit"
            className="p-1.5 rounded-md text-white/15 hover:text-white/40 hover:bg-white/[0.05] transition-colors cursor-pointer"
          >
            <Pencil className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onDelete}
            title="Delete"
            className="p-1.5 rounded-md text-white/15 hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <GoalProgress
        current={goal.current_amount}
        target={goal.target_amount}
      />

      {daysLeft !== null && (
        <div className="flex items-center gap-1.5 mt-3">
          <Calendar className="w-3 h-3 text-white/20" />
          <span
            className={`text-xs ${
              daysLeft < 0
                ? "text-red-400"
                : daysLeft < 30
                  ? "text-amber-400"
                  : "text-white/30"
            }`}
          >
            {daysLeft < 0
              ? `${Math.abs(daysLeft)} days overdue`
              : daysLeft === 0
                ? "Due today"
                : `${daysLeft} days left`}
          </span>
        </div>
      )}
    </div>
  );
}
